#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

// ─── CONFIGURACIÓN I2C ESP8266 ────────────────────────────────
#define SDA_PIN 4  // D2
#define SCL_PIN 5  // D1

MAX30105 particleSensor;

// ─── VARIABLES ───────────────────────────────────────────────
const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0;
int beatAvg = 0;

void setup() {
    Serial.begin(115200);
    delay(500);

    Wire.begin(SDA_PIN, SCL_PIN);

    Serial.println("\n🚀 Iniciando MAX30102...");

    if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
        Serial.println("❌ MAX30102 no encontrado.");
        Serial.println("   Revisa: VIN→3.3V, GND→GND, SDA→D2, SCL→D1");
        while (true) delay(1000);
    }

    Serial.println("✅ Sensor encontrado!");

    particleSensor.setup(
        60,   // Brillo LED
        4,    // Promedio de muestras
        2,    // Modo: Red + IR
        100,  // Frecuencia de muestreo
        411,  // Ancho de pulso
        4096  // Rango ADC
    );

    Serial.println("📡 Coloca tu dedo sobre el sensor...\n");
}

// ─── CÁLCULO MANUAL DE SPO2 ───────────────────────────────────
// Basado en la relación R = (AC_red/DC_red) / (AC_ir/DC_ir)
#define BUFFER_SIZE 50
long redBuffer[BUFFER_SIZE];
long irBuffer[BUFFER_SIZE];
int bufIndex = 0;
bool bufferFull = false;

float calculateSpO2() {
    long redAC = 0, irAC = 0;
    long redDC = 0, irDC = 0;

    int count = bufferFull ? BUFFER_SIZE : bufIndex;
    if (count < 10) return 0;

    for (int i = 0; i < count; i++) {
        redDC += redBuffer[i];
        irDC  += irBuffer[i];
    }
    redDC /= count;
    irDC  /= count;

    for (int i = 0; i < count; i++) {
        redAC += abs(redBuffer[i] - redDC);
        irAC  += abs(irBuffer[i]  - irDC);
    }

    if (irAC == 0 || irDC == 0) return 0;

    float R = ((float)redAC / redDC) / ((float)irAC / irDC);
    float spo2 = 110.0 - 25.0 * R; // fórmula empírica estándar

    if (spo2 > 100) spo2 = 100;
    if (spo2 < 80)  spo2 = 0; // lectura inválida
    return spo2;
}

void loop() {
    // Leer sensor
    particleSensor.check();
    if (!particleSensor.available()) return;

    long irValue  = particleSensor.getIR();
    long redValue = particleSensor.getRed();
    particleSensor.nextSample();

    // Guardar en buffer circular
    redBuffer[bufIndex] = redValue;
    irBuffer[bufIndex]  = irValue;
    bufIndex++;
    if (bufIndex >= BUFFER_SIZE) {
        bufIndex = 0;
        bufferFull = true;
    }

    // ─── Detección de latido ──────────────────────────────
    if (checkForBeat(irValue)) {
        long delta = millis() - lastBeat;
        lastBeat = millis();
        beatsPerMinute = 60 / (delta / 1000.0);

        if (beatsPerMinute > 20 && beatsPerMinute < 255) {
            rates[rateSpot++] = (byte)beatsPerMinute;
            rateSpot %= RATE_SIZE;

            beatAvg = 0;
            for (byte x = 0; x < RATE_SIZE; x++)
                beatAvg += rates[x];
            beatAvg /= RATE_SIZE;
        }

        // ─── Imprimir al detectar latido ─────────────────
        float spo2 = calculateSpO2();

        Serial.print("💓 BPM: ");
        Serial.print(beatsPerMinute, 1);
        Serial.print("  Promedio: ");
        Serial.print(beatAvg);
        Serial.print("  |  🫁 SpO2: ");

        if (spo2 > 0) {
            Serial.print(spo2, 1);
            Serial.print("%");
        } else {
            Serial.print("Calculando...");
        }

        Serial.print("  |  Estado: ");
        if (irValue < 50000) {
            Serial.println("⚠️  Sin dedo");
        } else if (spo2 > 0 && spo2 < 94) {
            Serial.println("🔴 SpO2 baja");
        } else if (beatAvg > 100) {
            Serial.println("🟡 Taquicardia");
        } else if (beatAvg < 50 && beatAvg > 0) {
            Serial.println("🟡 Bradicardia");
        } else {
            Serial.println("🟢 Normal");
        }
    }

    // Aviso si no hay dedo
    if (irValue < 50000) {
        static uint32_t lastMsg = 0;
        if (millis() - lastMsg > 2000) {
            Serial.println("📡 Esperando dedo...");
            lastMsg = millis();
        }
    }
}