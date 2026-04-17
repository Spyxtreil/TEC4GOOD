/*
  Pulso simple con MAX30102 y Arduino Nano
  --------------------------------------------------
  Librería necesaria (instalar desde el Library Manager del IDE de Arduino):
    "SparkFun MAX3010x Pulse and Proximity Sensor Library"  by SparkFun

  Conexiones (Arduino Nano <-> MAX30102):
    VIN  -> 3.3V  (NO uses 5V directamente al sensor)
    GND  -> GND
    SDA  -> A4
    SCL  -> A5

  Cómo usarlo:
    1. Sube este código al Nano.
    2. Abre el Monitor Serie a 115200 baudios.
    3. Coloca la yema del dedo sobre el sensor, sin apretar mucho, y espera
       unos segundos a que se estabilice la lectura.
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
  Serial.println("Iniciando MAX30102...");

  // Inicializa el sensor por I2C a velocidad estándar
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("No se encontro el MAX30102. Revisa el cableado.");
    while (1);
  }

  Serial.println("Coloca tu dedo en el sensor con presion ligera.");

  // Configuración básica recomendada por SparkFun
  particleSensor.setup();                    // configuración por defecto
  particleSensor.setPulseAmplitudeRed(0x0A); // LED rojo bajo (solo para indicar que está encendido)
  particleSensor.setPulseAmplitudeGreen(0);  // apaga el LED verde (MAX30102 no lo tiene, por seguridad)
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
