/*
  =============================================================
    TEC4GOOD — Pulso + SpO2 con MAX30102 sobre BLE (ESP32)
  =============================================================

  DISCLAIMER:
    Sketch educativo / prototipo. NO es un dispositivo medico.
    Ver TERMS_AND_CONDITIONS.md en la raiz del repo.

  Requisitos (Arduino Library Manager):
    - "SparkFun MAX3010x Pulse and Proximity Sensor Library"
    - ESP32 Core (boards manager -> esp32 by Espressif)

  Placa:
    ESP32 Dev Module (o similar).
    SDA = GPIO 21, SCL = GPIO 22, VIN = 3.3V, GND = GND.

  Protocolo BLE:
    Service UUID: 0000FEED-0000-1000-8000-00805F9B34FB
    DATA   char  0000FEE1 (notify): "timestamp_ms,ir,red,bpm,spo2\n"
    COMMAND char 0000FEE2 (write) : 1 char -> c/s/l/r/g/?
*/

#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <EEPROM.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ─── BLE UUIDs ─────────────────────────────────────────────────
#define SVC_UUID   "0000FEED-0000-1000-8000-00805F9B34FB"
#define DATA_UUID  "0000FEE1-0000-1000-8000-00805F9B34FB"
#define CMD_UUID   "0000FEE2-0000-1000-8000-00805F9B34FB"

BLEServer*          bleServer = nullptr;
BLECharacteristic*  dataChar  = nullptr;
BLECharacteristic*  cmdChar   = nullptr;
bool                bleConnected = false;

// ─── Sensor ────────────────────────────────────────────────────
MAX30105 particleSensor;

enum Mode { MODE_BOOT, MODE_CALIBRATE, MODE_MEASURE };
Mode mode = MODE_BOOT;

const byte RATE_SIZE = 8;
byte rates[RATE_SIZE];
byte rateSpot = 0;
unsigned long lastBeat = 0;
float beatsPerMinute = 0;
int   beatAvg = 0;

#define SPO2_BUFFER 100
uint32_t redBuffer[SPO2_BUFFER];
uint32_t irBuffer[SPO2_BUFFER];
int  bufIndex = 0;
bool bufferFull = false;

// ─── Calibracion (persistente en EEPROM) ──────────────────────
struct Calib {
  float spo2_a;
  float spo2_b;
  long  finger_threshold;
  bool  calibrated;
};

Calib calib = {110.0f, 25.0f, 50000L, false};

#define CALIB_MAGIC 0xC41B0002u
#define CALIB_ADDR  0

struct StoredCalib {
  uint32_t magic;
  Calib    data;
  uint16_t checksum;
};

static uint16_t calibChecksum(const Calib &c) {
  const uint8_t *p = (const uint8_t *)&c;
  uint16_t sum = 0;
  for (size_t i = 0; i < sizeof(Calib); i++) sum ^= (uint16_t)p[i] << (i & 7);
  return sum;
}

bool saveCalibToEEPROM() {
  StoredCalib sc{ CALIB_MAGIC, calib, calibChecksum(calib) };
  EEPROM.begin(sizeof(StoredCalib) + 4);
  EEPROM.put(CALIB_ADDR, sc);
  bool ok = EEPROM.commit();
  EEPROM.end();
  return ok;
}

bool loadCalibFromEEPROM() {
  StoredCalib sc;
  EEPROM.begin(sizeof(StoredCalib) + 4);
  EEPROM.get(CALIB_ADDR, sc);
  EEPROM.end();
  if (sc.magic != CALIB_MAGIC) return false;
  if (sc.checksum != calibChecksum(sc.data)) return false;
  if (sc.data.spo2_a < 80 || sc.data.spo2_a > 150) return false;
  if (sc.data.spo2_b < 10 || sc.data.spo2_b > 60)  return false;
  if (sc.data.finger_threshold < 10000L)           return false;
  calib = sc.data;
  return true;
}

inline bool fingerPresent(long ir) { return ir > calib.finger_threshold; }

// ─── BLE helpers ───────────────────────────────────────────────
void bleNotifyLine(const String &s) {
  if (!bleConnected || !dataChar) return;
  dataChar->setValue((uint8_t*)s.c_str(), s.length());
  dataChar->notify();
}

void bleNotifyMessage(const String &msg) {
  bleNotifyLine("# " + msg + "\n");
  Serial.println(msg);
}

// ─── SpO2 (RMS) ────────────────────────────────────────────────
float calculateSpO2() {
  int count = bufferFull ? SPO2_BUFFER : bufIndex;
  if (count < 50) return -1.0f;

  double redDC = 0, irDC = 0;
  for (int i = 0; i < count; i++) { redDC += redBuffer[i]; irDC += irBuffer[i]; }
  redDC /= count; irDC /= count;
  if (redDC <= 0 || irDC <= 0) return -1.0f;

  double redAC2 = 0, irAC2 = 0;
  for (int i = 0; i < count; i++) {
    double dr = (double)redBuffer[i] - redDC;
    double di = (double)irBuffer[i]  - irDC;
    redAC2 += dr * dr; irAC2 += di * di;
  }
  double redAC = sqrt(redAC2 / count);
  double irAC  = sqrt(irAC2  / count);
  if (irAC == 0) return -1.0f;

  double R = (redAC / redDC) / (irAC / irDC);
  double spo2 = calib.spo2_a - calib.spo2_b * R;
  if (spo2 > 100.0) spo2 = 100.0;
  if (spo2 < 70.0)  return -1.0f;
  return (float)spo2;
}

// ─── Calibracion ───────────────────────────────────────────────
void runCalibration() {
  bleNotifyMessage("CALIBRACION iniciada");
  bleNotifyMessage("Paso 1/2: dedo quieto 30s");
  delay(5000);

  unsigned long t0 = millis();
  unsigned long samples = 0;
  double irSumFinger = 0;
  while (millis() - t0 < 30000UL) {
    particleSensor.check();
    while (particleSensor.available()) {
      irSumFinger += particleSensor.getIR();
      samples++;
      particleSensor.nextSample();
    }
    delay(1);
  }
  if (samples == 0) { bleNotifyMessage("calibracion cancelada"); return; }
  double irFinger = irSumFinger / samples;

  bleNotifyMessage("Paso 2/2: retira el dedo 15s");
  delay(5000);
  t0 = millis(); samples = 0;
  double irSumNo = 0;
  while (millis() - t0 < 15000UL) {
    particleSensor.check();
    while (particleSensor.available()) {
      irSumNo += particleSensor.getIR();
      samples++;
      particleSensor.nextSample();
    }
    delay(1);
  }
  if (samples == 0) { bleNotifyMessage("calibracion cancelada"); return; }
  double irNo = irSumNo / samples;

  long threshold = (long)((irFinger + irNo) / 2.0);
  if (threshold < 20000) threshold = 20000;
  calib.finger_threshold = threshold;
  calib.calibrated = true;

  bleNotifyMessage(String("threshold=") + threshold);
  bleNotifyMessage("CALIBRACION OK");
}

// ─── Callbacks BLE ─────────────────────────────────────────────
class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*)    override { bleConnected = true;  Serial.println("[BLE] conectado"); }
  void onDisconnect(BLEServer* s) override {
    bleConnected = false;
    Serial.println("[BLE] desconectado");
    s->startAdvertising();
  }
};

class CmdCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    std::string v = c->getValue();
    if (v.empty()) return;
    char cmd = v[0];
    switch (cmd) {
      case 'c': case 'C': mode = MODE_CALIBRATE; break;
      case 's': case 'S':
        bleNotifyMessage(saveCalibToEEPROM() ? "calibracion guardada" : "error guardando");
        break;
      case 'l': case 'L':
        bleNotifyMessage(loadCalibFromEEPROM() ? "calibracion cargada" : "no hay calibracion valida");
        break;
      case 'r': case 'R':
        calib = {110.0f, 25.0f, 50000L, false};
        bleNotifyMessage("reset a fabrica");
        break;
      case 'g': case 'G':
        bleNotifyMessage("CSV siempre activo en este build");
        break;
      case '?':
        bleNotifyMessage("comandos: c s l r g ?");
        break;
      default:
        bleNotifyMessage(String("desconocido: ") + cmd);
        break;
    }
  }
};

// ─── setup ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("\n=== TEC4GOOD — ESP32 BLE ===");
  Serial.println("AVISO: dispositivo educativo. NO es un oximetro medico.");

  if (loadCalibFromEEPROM()) Serial.println("Calibracion cargada de EEPROM.");
  else                       Serial.println("Usando calibracion de fabrica.");

  Wire.begin(21, 22);

  unsigned long t0 = millis();
  bool ok = false;
  while (millis() - t0 < 10000UL) {
    if (particleSensor.begin(Wire, I2C_SPEED_FAST)) { ok = true; break; }
    Serial.println("Sensor no encontrado, reintentando...");
    delay(1000);
  }
  if (!ok) {
    Serial.println("ERROR: MAX30102 no responde.");
    while (true) { delay(2000); Serial.println("revisa cableado."); }
  }
  particleSensor.setup(60, 4, 2, 100, 411, 4096);

  // BLE init
  BLEDevice::init("TEC4GOOD");
  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new ServerCB());

  BLEService* svc = bleServer->createService(SVC_UUID);

  dataChar = svc->createCharacteristic(
    DATA_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  dataChar->addDescriptor(new BLE2902());

  cmdChar = svc->createCharacteristic(
    CMD_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  cmdChar->setCallbacks(new CmdCB());

  svc->start();

  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SVC_UUID);
  adv->setScanResponse(true);
  adv->setMinPreferred(0x06);
  adv->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("BLE advertising como 'TEC4GOOD'");
  mode = MODE_MEASURE;
}

// ─── loop ──────────────────────────────────────────────────────
void loop() {
  if (mode == MODE_CALIBRATE) {
    runCalibration();
    mode = MODE_MEASURE;
    return;
  }

  particleSensor.check();
  if (!particleSensor.available()) { delay(1); return; }

  uint32_t ir  = particleSensor.getIR();
  uint32_t red = particleSensor.getRed();
  particleSensor.nextSample();

  redBuffer[bufIndex] = red;
  irBuffer[bufIndex]  = ir;
  bufIndex++;
  if (bufIndex >= SPO2_BUFFER) { bufIndex = 0; bufferFull = true; }

  if (fingerPresent((long)ir) && checkForBeat((long)ir)) {
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
  }

  // Publicar un paquete cada 100 ms (10 Hz)
  static unsigned long lastPub = 0;
  if (millis() - lastPub >= 100) {
    lastPub = millis();
    float spo2 = calculateSpO2();

    String line = String(lastPub) + "," +
                  String(ir) + "," +
                  String(red) + "," +
                  String(beatsPerMinute, 1) + "," +
                  (spo2 > 0 ? String(spo2, 1) : String("")) + "\n";
    Serial.print(line);
    bleNotifyLine(line);
  }

  delay(1);
}
