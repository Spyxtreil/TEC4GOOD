/*
  Pulso simple con MAX30102 y Arduino Nano / Uno
  --------------------------------------------------
  DISCLAIMER:
    Este sketch es de PROTOTIPADO y USO EDUCATIVO. NO es un
    dispositivo medico y NO debe usarse para diagnostico ni
    toma de decisiones clinicas. Ver TERMS_AND_CONDITIONS.md
    en la raiz del repositorio.

  Libreria necesaria (instalar desde el Library Manager del IDE de Arduino):
    "SparkFun MAX3010x Pulse and Proximity Sensor Library"  by SparkFun

  Conexiones (Arduino Nano / Uno <-> MAX30102):
    VIN  -> 3.3V  (NO uses 5V directamente al sensor)
    GND  -> GND
    SDA  -> A4
    SCL  -> A5

  Como usarlo:
    1. Sube este codigo al Arduino.
    2. Abre el Monitor Serie a 115200 baudios.
    3. Coloca la yema del dedo sobre el sensor, sin apretar mucho, y espera
       unos segundos a que se estabilice la lectura.

  Para la version completa con SpO2, calibracion y comandos por
  serial, ver sensooooor2.ino.
*/

#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 particleSensor;

const byte RATE_SIZE = 4;      // promedio de las últimas N pulsaciones
byte rates[RATE_SIZE];         // arreglo de BPM
byte rateSpot = 0;
long lastBeat = 0;             // tiempo del último latido detectado

float beatsPerMinute;
int beatAvg;

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println(F("==============================================="));
  Serial.println(F("  AVISO: dispositivo educativo / prototipo."));
  Serial.println(F("  NO es un oximetro medico. Ver TERMS_AND_"));
  Serial.println(F("  CONDITIONS.md antes de usar."));
  Serial.println(F("==============================================="));
  Serial.println(F("Iniciando MAX30102..."));

  // Reintento con timeout en vez de bloquear para siempre.
  const unsigned long startT = millis();
  bool ok = false;
  while (millis() - startT < 10000UL) {
    if (particleSensor.begin(Wire, I2C_SPEED_STANDARD)) { ok = true; break; }
    Serial.println(F("  Sensor no encontrado. Reintentando..."));
    delay(1000);
  }
  if (!ok) {
    Serial.println(F("ERROR: MAX30102 no responde. Revisa el cableado."));
    while (true) {
      delay(3000);
      Serial.println(F("  (sin sensor) reinicia tras revisar conexiones."));
    }
  }

  Serial.println(F("Coloca tu dedo en el sensor con presion ligera."));

  // Configuracion basica recomendada por SparkFun
  particleSensor.setup();                    // configuracion por defecto
  particleSensor.setPulseAmplitudeRed(0x0A); // LED rojo bajo (indicador)
  particleSensor.setPulseAmplitudeGreen(0);  // MAX30102 no tiene verde; por seguridad
}

void loop() {
  long irValue = particleSensor.getIR();

  // checkForBeat detecta un latido a partir de la señal IR
  if (checkForBeat(irValue)) {
    long delta = millis() - lastBeat;
    lastBeat = millis();

    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;

      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++) beatAvg += rates[x];
      beatAvg /= RATE_SIZE;
    }
  }

  Serial.print("IR=");
  Serial.print(irValue);
  Serial.print(", BPM=");
  Serial.print(beatsPerMinute, 1);
  Serial.print(", Prom BPM=");
  Serial.print(beatAvg);

  if (irValue < 50000) Serial.print(" -> Sin dedo");

  Serial.println();
}
