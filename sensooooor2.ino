/*
  =============================================================
    Pulso + SpO2 con MAX30102
    Portable: Arduino Uno / Nano / ESP8266 / ESP32
  =============================================================

  DISCLAIMER:
    Este sketch es de PROTOTIPADO y USO EDUCATIVO.
    NO es un dispositivo medico, NO esta calibrado clinicamente
    y NO debe usarse para diagnostico ni toma de decisiones
    clinicas. Ver TERMS_AND_CONDITIONS.md en la raiz del repo.

  Librerias requeridas (Arduino Library Manager):
    - "SparkFun MAX3010x Pulse and Proximity Sensor Library"

  Conexiones:
    Uno/Nano:   SDA = A4 , SCL = A5 , VIN = 3.3V
    ESP8266:    SDA = D2 , SCL = D1 , VIN = 3.3V
    ESP32:      SDA = 21 , SCL = 22 , VIN = 3.3V

  Uso:
    Monitor Serie a 115200 baudios.
    Comandos (enviar por el monitor serie):
      c  -> iniciar rutina de calibracion (60 s con dedo quieto)
      s  -> guardar calibracion actual en EEPROM
      l  -> cargar calibracion desde EEPROM
      r  -> reiniciar valores de calibracion a los de fabrica
      g  -> activar/desactivar log CSV (timestamp,ir,red,bpm,spo2)
      ?  -> mostrar ayuda

  Notas:
    - En AVR (Uno/Nano) se usa watchdog timer de 8 s para reiniciar
      si el loop se cuelga. En ESP se usa el watchdog nativo.
    - La calibracion sobrevive al reinicio si la guardas con 's'.
*/

#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

#if defined(ESP8266) || defined(ESP32)
  // ESP cores traen su propio watchdog; no incluimos avr/wdt.
#else
  #include <avr/wdt.h>
#endif

#include <EEPROM.h>

// ─── DETECCION DE PLATAFORMA ───────────────────────────────────
#if defined(ESP8266)
  #define SDA_PIN 4   // D2
  #define SCL_PIN 5   // D1
  #define HAS_WIRE_BEGIN_PINS 1
#elif defined(ESP32)
  #define SDA_PIN 21
  #define SCL_PIN 22
  #define HAS_WIRE_BEGIN_PINS 1
#else
  // AVR (Uno, Nano, Mega, etc.) — pines I2C son fijos en hardware.
  #define HAS_WIRE_BEGIN_PINS 0
#endif

MAX30105 particleSensor;

// ─── ESTADOS DEL PROGRAMA ──────────────────────────────────────
enum Mode { MODE_BOOT, MODE_CALIBRATE, MODE_MEASURE };
Mode mode = MODE_BOOT;

// ─── PARAMETROS DE LATIDO ──────────────────────────────────────
const byte RATE_SIZE = 8;       // promedio de ultimos N BPM
byte rates[RATE_SIZE];
byte rateSpot = 0;
unsigned long lastBeat = 0;
float beatsPerMinute = 0;
int   beatAvg = 0;

// ─── BUFFER CIRCULAR PARA SpO2 ─────────────────────────────────
// 100 Hz * 4 s = 400 muestras -> memoria Uno/Nano insuficiente.
// Compromiso: 100 muestras (~1 s a 100 Hz).
#define SPO2_BUFFER 100
uint32_t redBuffer[SPO2_BUFFER];
uint32_t irBuffer[SPO2_BUFFER];
int  bufIndex = 0;
bool bufferFull = false;

// ─── CALIBRACION ───────────────────────────────────────────────
// spo2 = spo2_a - spo2_b * R
// Valores de fabrica (aproximacion estandar MAX30102).
struct Calib {
  float spo2_a;
  float spo2_b;
  long  finger_threshold;  // umbral IR para considerar "hay dedo"
  bool  calibrated;
};

Calib calib = {110.0f, 25.0f, 50000L, false};

// ─── EEPROM LAYOUT ─────────────────────────────────────────────
// Magic number que identifica que los bytes siguientes son nuestra
// estructura Calib. Si cambias el layout, incrementa este valor.
#define CALIB_MAGIC   0xC41B0002u
#define CALIB_ADDR    0

struct StoredCalib {
  uint32_t magic;
  Calib    data;
  uint16_t checksum;  // suma simple XOR para detectar corrupcion
};

static uint16_t calibChecksum(const Calib &c) {
  const uint8_t *p = (const uint8_t *)&c;
  uint16_t sum = 0;
  for (size_t i = 0; i < sizeof(Calib); i++) sum ^= (uint16_t)p[i] << (i & 7);
  return sum;
}

// ─── LOG CSV ───────────────────────────────────────────────────
bool csvLogging = false;
bool csvHeaderPrinted = false;

// ─── UMBRALES DE PRESENCIA DE DEDO ─────────────────────────────
inline bool fingerPresent(long irValue) {
  return irValue > calib.finger_threshold;
}

// ─── PROMPT DE DISCLAIMER ──────────────────────────────────────
void printDisclaimer() {
  Serial.println();
  Serial.println(F("================================================"));
  Serial.println(F("  AVISO: Dispositivo educativo / prototipo."));
  Serial.println(F("  NO es un oximetro medico. NO usar para"));
  Serial.println(F("  diagnostico ni decisiones clinicas."));
  Serial.println(F("  Ver TERMS_AND_CONDITIONS.md en el repo."));
  Serial.println(F("================================================"));
  Serial.println();
}

void printHelp() {
  Serial.println(F("Comandos disponibles:"));
  Serial.println(F("  c -> iniciar calibracion (60 s, dedo quieto)"));
  Serial.println(F("  s -> guardar calibracion en EEPROM"));
  Serial.println(F("  l -> cargar calibracion desde EEPROM"));
  Serial.println(F("  r -> reset calibracion a valores de fabrica"));
  Serial.println(F("  g -> activar/desactivar log CSV"));
  Serial.println(F("  ? -> mostrar esta ayuda"));
  Serial.println();
}

// ─── EEPROM HELPERS ────────────────────────────────────────────
bool saveCalibToEEPROM() {
  StoredCalib sc;
  sc.magic    = CALIB_MAGIC;
  sc.data     = calib;
  sc.checksum = calibChecksum(calib);
#if defined(ESP8266) || defined(ESP32)
  EEPROM.begin(sizeof(StoredCalib) + 4);
  EEPROM.put(CALIB_ADDR, sc);
  bool ok = EEPROM.commit();
  EEPROM.end();
  return ok;
#else
  EEPROM.put(CALIB_ADDR, sc);
  return true;  // EEPROM.put en AVR no devuelve estado
#endif
}

bool loadCalibFromEEPROM() {
  StoredCalib sc;
#if defined(ESP8266) || defined(ESP32)
  EEPROM.begin(sizeof(StoredCalib) + 4);
  EEPROM.get(CALIB_ADDR, sc);
  EEPROM.end();
#else
  EEPROM.get(CALIB_ADDR, sc);
#endif
  if (sc.magic != CALIB_MAGIC) return false;
  if (sc.checksum != calibChecksum(sc.data)) return false;
  // Sanity checks
  if (sc.data.spo2_a < 80 || sc.data.spo2_a > 150) return false;
  if (sc.data.spo2_b < 10 || sc.data.spo2_b > 60)  return false;
  if (sc.data.finger_threshold < 10000L)           return false;
  calib = sc.data;
  return true;
}

// ─── WATCHDOG HELPERS ──────────────────────────────────────────
inline void wdtSetup() {
#if defined(ESP8266) || defined(ESP32)
  // ESP core arranca su propio watchdog; nada que hacer aqui.
#else
  wdt_enable(WDTO_8S);
#endif
}

inline void wdtKick() {
#if defined(ESP8266)
  yield();           // permite al scheduler de ESP resetear el WDT
#elif defined(ESP32)
  // nada — el scheduler de FreeRTOS alimenta el WDT entre tareas
#else
  wdt_reset();
#endif
}

// ─── SpO2 ──────────────────────────────────────────────────────
// Calcula R = (AC_red/DC_red) / (AC_ir/DC_ir) con media cuadratica
// para AC (mas estable que abs()).
float calculateSpO2() {
  int count = bufferFull ? SPO2_BUFFER : bufIndex;
  if (count < 50) return -1.0f;        // no hay muestras suficientes

  // DC = media aritmetica
  double redDC = 0, irDC = 0;
  for (int i = 0; i < count; i++) {
    redDC += redBuffer[i];
    irDC  += irBuffer[i];
  }
  redDC /= count;
  irDC  /= count;

  if (redDC <= 0 || irDC <= 0) return -1.0f;

  // AC = RMS de la senal centrada
  double redAC2 = 0, irAC2 = 0;
  for (int i = 0; i < count; i++) {
    double dr = (double)redBuffer[i] - redDC;
    double di = (double)irBuffer[i]  - irDC;
    redAC2 += dr * dr;
    irAC2  += di * di;
  }
  double redAC = sqrt(redAC2 / count);
  double irAC  = sqrt(irAC2  / count);

  if (irAC == 0) return -1.0f;

  double R = (redAC / redDC) / (irAC / irDC);
  double spo2 = calib.spo2_a - calib.spo2_b * R;

  if (spo2 > 100.0) spo2 = 100.0;
  if (spo2 < 70.0)  return -1.0f;       // fuera de rango plausible
  return (float)spo2;
}

// ─── RUTINA DE CALIBRACION ─────────────────────────────────────
// Estrategia:
//   1. Durante 60 s con dedo quieto, registra el valor medio de IR
//      cuando hay dedo y el valor medio cuando NO hay dedo (pide al
//      usuario retirar el dedo los ultimos 10 s).
//   2. Ajusta finger_threshold al punto medio entre ambos.
//   3. Si el usuario declara una SpO2 de referencia (por ejemplo de
//      un oximetro medico), ajusta spo2_a para que la medicion
//      coincida; spo2_b se mantiene.
void runCalibration() {
  Serial.println(F(">>> CALIBRACION INICIADA"));
  Serial.println(F("Paso 1/3: coloca el dedo sobre el sensor y manten"));
  Serial.println(F("          quieto durante 30 segundos."));
  Serial.println(F("          (empieza en 5 s...)"));
  for (int i = 5; i > 0; i--) { Serial.print(i); Serial.print(' '); delay(1000); }
  Serial.println();

  // Paso 1: valor IR con dedo
  unsigned long t0 = millis();
  unsigned long samples = 0;
  double irSumFinger = 0;
  while (millis() - t0 < 30000UL) {
    wdtKick();
    particleSensor.check();
    while (particleSensor.available()) {
      long ir = particleSensor.getIR();
      irSumFinger += ir;
      samples++;
      particleSensor.nextSample();
    }
    if ((millis() - t0) % 5000 < 50) {
      Serial.print(F("  ... "));
      Serial.print((millis() - t0) / 1000);
      Serial.println(F("s"));
      delay(100);
    }
  }
  if (samples == 0) {
    Serial.println(F("!! Sin muestras. Calibracion abortada."));
    return;
  }
  double irFingerAvg = irSumFinger / samples;
  Serial.print(F("  IR promedio con dedo: "));
  Serial.println((long)irFingerAvg);

  // Paso 2: valor IR sin dedo
  Serial.println(F("Paso 2/3: retira el dedo. Espera 15 segundos."));
  for (int i = 5; i > 0; i--) { Serial.print(i); Serial.print(' '); delay(1000); }
  Serial.println();

  t0 = millis();
  samples = 0;
  double irSumNoFinger = 0;
  while (millis() - t0 < 15000UL) {
    wdtKick();
    particleSensor.check();
    while (particleSensor.available()) {
      long ir = particleSensor.getIR();
      irSumNoFinger += ir;
      samples++;
      particleSensor.nextSample();
    }
  }
  if (samples == 0) {
    Serial.println(F("!! Sin muestras. Calibracion abortada."));
    return;
  }
  double irNoFingerAvg = irSumNoFinger / samples;
  Serial.print(F("  IR promedio sin dedo: "));
  Serial.println((long)irNoFingerAvg);

  // Fija el umbral al punto medio, con un minimo de seguridad.
  long threshold = (long)((irFingerAvg + irNoFingerAvg) / 2.0);
  if (threshold < 20000) threshold = 20000;
  calib.finger_threshold = threshold;
  calib.calibrated = true;

  Serial.print(F("  Nuevo umbral de dedo: "));
  Serial.println(threshold);

  // Paso 3: ajuste opcional de SpO2
  Serial.println(F("Paso 3/3: opcional -- ajuste contra oximetro de"));
  Serial.println(F("          referencia. Vuelve a colocar el dedo."));
  Serial.println(F("          (saltar este paso = enviar 0)"));
  Serial.println(F("  Introduce la SpO2 de referencia (80-100) y ENTER:"));

  // Espera entrada serial con timeout de 30 s
  unsigned long waitStart = millis();
  String line = "";
  while (millis() - waitStart < 30000UL) {
    wdtKick();
    while (Serial.available()) {
      char ch = (char)Serial.read();
      if (ch == '\n' || ch == '\r') {
        if (line.length() > 0) goto have_line;
      } else {
        line += ch;
      }
    }
    delay(10);
  }
have_line:
  float ref = line.toFloat();
  if (ref >= 80.0f && ref <= 100.0f) {
    // Mide la lectura actual durante 10 s y ajusta spo2_a.
    bufIndex = 0; bufferFull = false;
    unsigned long measT0 = millis();
    while (millis() - measT0 < 10000UL) {
      wdtKick();
      particleSensor.check();
      while (particleSensor.available()) {
        redBuffer[bufIndex] = particleSensor.getRed();
        irBuffer[bufIndex]  = particleSensor.getIR();
        bufIndex++;
        if (bufIndex >= SPO2_BUFFER) { bufIndex = 0; bufferFull = true; }
        particleSensor.nextSample();
      }
    }
    float measured = calculateSpO2();
    if (measured > 0) {
      float delta = ref - measured;
      calib.spo2_a += delta;  // offset simple
      Serial.print(F("  Offset aplicado: "));
      Serial.println(delta, 2);
      Serial.print(F("  Nuevo spo2_a: "));
      Serial.println(calib.spo2_a, 2);
    } else {
      Serial.println(F("  Lectura no valida, se omite ajuste."));
    }
  } else {
    Serial.println(F("  Ajuste de SpO2 omitido."));
  }

  Serial.println(F(">>> CALIBRACION TERMINADA"));
  Serial.println();
}

// ─── COMANDOS SERIAL ───────────────────────────────────────────
void handleSerialCommand() {
  if (!Serial.available()) return;
  char c = (char)Serial.read();
  // descarta whitespace
  while (c == '\n' || c == '\r' || c == ' ') {
    if (!Serial.available()) return;
    c = (char)Serial.read();
  }
  switch (c) {
    case 'c': case 'C':
      mode = MODE_CALIBRATE;
      break;
    case 's': case 'S':
      if (saveCalibToEEPROM()) Serial.println(F("Calibracion guardada en EEPROM."));
      else                     Serial.println(F("ERROR al guardar en EEPROM."));
      break;
    case 'l': case 'L':
      if (loadCalibFromEEPROM()) Serial.println(F("Calibracion cargada desde EEPROM."));
      else                       Serial.println(F("No hay calibracion valida guardada."));
      break;
    case 'r': case 'R':
      calib = {110.0f, 25.0f, 50000L, false};
      Serial.println(F("Calibracion reseteada a valores de fabrica."));
      break;
    case 'g': case 'G':
      csvLogging = !csvLogging;
      csvHeaderPrinted = false;
      Serial.print(F("Log CSV: "));
      Serial.println(csvLogging ? F("ON") : F("OFF"));
      break;
    case '?':
      printHelp();
      break;
    default:
      Serial.print(F("Comando desconocido: "));
      Serial.println(c);
      printHelp();
      break;
  }
}

// ─── SETUP ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  printDisclaimer();
  wdtSetup();

#if HAS_WIRE_BEGIN_PINS
  Wire.begin(SDA_PIN, SCL_PIN);
#else
  Wire.begin();
#endif

  Serial.println(F("Iniciando MAX30102..."));

  // Intenta auto-cargar calibracion guardada
  if (loadCalibFromEEPROM()) {
    Serial.println(F("Calibracion guardada cargada desde EEPROM."));
  } else {
    Serial.println(F("Usando calibracion de fabrica (no hay guardada)."));
  }

  // Reintento con timeout en vez de bloquear para siempre.
  const unsigned long startT = millis();
  bool ok = false;
  while (millis() - startT < 10000UL) {
    wdtKick();
    if (particleSensor.begin(Wire, I2C_SPEED_FAST)) {
      ok = true;
      break;
    }
    Serial.println(F("  Sensor no encontrado. Reintentando..."));
    delay(1000);
  }
  if (!ok) {
    Serial.println(F("ERROR: MAX30102 no responde tras 10 s."));
    Serial.println(F("Revisa: VIN->3.3V, GND->GND, SDA/SCL correctos."));
    Serial.println(F("El sketch continuara en modo inactivo."));
    while (true) {
      wdtKick();
      delay(2000);
      Serial.println(F("  (sin sensor) -- reinicia el Arduino cuando"
                       " hayas revisado el cableado."));
    }
  }

  Serial.println(F("Sensor OK."));

  particleSensor.setup(
    60,     // brillo LED
    4,      // promedio de muestras
    2,      // modo: Red + IR
    100,    // frecuencia de muestreo (Hz)
    411,    // ancho de pulso (us)
    4096    // rango ADC
  );

  mode = MODE_MEASURE;
  printHelp();
  Serial.println(F("Coloca tu dedo sobre el sensor..."));
  Serial.println();
}

// ─── LOOP ──────────────────────────────────────────────────────
void loop() {
  wdtKick();
  handleSerialCommand();

  if (mode == MODE_CALIBRATE) {
    runCalibration();
    mode = MODE_MEASURE;
    return;
  }

  particleSensor.check();
  if (!particleSensor.available()) return;

  uint32_t irValue  = particleSensor.getIR();
  uint32_t redValue = particleSensor.getRed();
  particleSensor.nextSample();

  redBuffer[bufIndex] = redValue;
  irBuffer[bufIndex]  = irValue;
  bufIndex++;
  if (bufIndex >= SPO2_BUFFER) {
    bufIndex = 0;
    bufferFull = true;
  }

  // Log CSV crudo (alta frecuencia) si esta activado
  if (csvLogging) {
    if (!csvHeaderPrinted) {
      Serial.println(F("# CSV: timestamp_ms,ir,red,bpm,spo2"));
      csvHeaderPrinted = true;
    }
    float spo2_now = calculateSpO2();
    Serial.print(millis());        Serial.print(',');
    Serial.print(irValue);         Serial.print(',');
    Serial.print(redValue);        Serial.print(',');
    Serial.print(beatsPerMinute, 1); Serial.print(',');
    if (spo2_now > 0) Serial.println(spo2_now, 1);
    else              Serial.println(F(""));
  }

  // Detectar latido solo si hay dedo
  if (fingerPresent((long)irValue) && checkForBeat((long)irValue)) {
    unsigned long now = millis();
    unsigned long delta = now - lastBeat;
    lastBeat = now;

    if (delta > 0) {
      float bpm = 60000.0f / (float)delta;
      if (bpm > 30 && bpm < 220) {
        beatsPerMinute = bpm;
        rates[rateSpot++] = (byte)bpm;
        rateSpot %= RATE_SIZE;

        int sum = 0;
        for (byte x = 0; x < RATE_SIZE; x++) sum += rates[x];
        beatAvg = sum / RATE_SIZE;
      }
    }

    float spo2 = calculateSpO2();

    Serial.print(F("BPM: "));
    Serial.print(beatsPerMinute, 1);
    Serial.print(F("  Prom: "));
    Serial.print(beatAvg);
    Serial.print(F("  SpO2: "));
    if (spo2 > 0) { Serial.print(spo2, 1); Serial.print('%'); }
    else          { Serial.print(F("---")); }

    Serial.print(F("  Estado: "));
    // IMPORTANTE: las etiquetas aqui NO son diagnosticos medicos.
    // Son descriptores numericos; siempre imprimimos [NO DIAGNOSTICO].
    if (spo2 > 0 && spo2 < 94)       Serial.print(F("SpO2 baja"));
    else if (beatAvg > 100)          Serial.print(F("Frecuencia alta"));
    else if (beatAvg > 0 && beatAvg < 50) Serial.print(F("Frecuencia baja"));
    else                             Serial.print(F("Dentro de rango"));
    Serial.println(F(" [NO DIAGNOSTICO]"));
  }

  // Mensaje periodico si no hay dedo
  if (!fingerPresent((long)irValue)) {
    static unsigned long lastMsg = 0;
    if (millis() - lastMsg > 3000UL) {
      Serial.println(F("Esperando dedo..."));
      lastMsg = millis();
    }
  }
}
