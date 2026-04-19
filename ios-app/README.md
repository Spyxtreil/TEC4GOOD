# TEC4GOOD — iOS app

App iOS nativa en SwiftUI que se conecta por Bluetooth LE a un ESP32
con MAX30102 y muestra pulso (BPM) y SpO₂ en tiempo real.

> ⚠️ **No es un dispositivo médico.** Ver [`../TERMS_AND_CONDITIONS.md`](../TERMS_AND_CONDITIONS.md).

## Requisitos

- **Mac** con macOS 14 (Sonoma) o más reciente.
- **Xcode 15+** (gratis en Mac App Store).
- **iPhone** con iOS 17+ (para probar en físico) o el simulador de Xcode.
- **ESP32** con el sketch `arduino/sensooooor2_ble/sensooooor2_ble.ino` flasheado. Sin el ESP32 la app corre en **modo demo** con datos simulados.
- [`xcodegen`](https://github.com/yonaskolb/XcodeGen) (solo si quieres regenerar el proyecto desde `project.yml`).

## Estructura

```
ios-app/
├── project.yml                 # Fuente de verdad: xcodegen lo usa para armar el .xcodeproj
├── TEC4GOOD.xcodeproj/         # Generado
└── TEC4GOOD/
    ├── TEC4GOODApp.swift       # @main
    ├── ContentView.swift       # root + gate de Términos
    ├── Models/
    │   ├── Reading.swift       # BPM + SpO2 + IR + red
    │   ├── Session.swift       # grupo de lecturas
    │   └── CalibrationState.swift
    ├── Services/
    │   ├── BluetoothManager.swift  # CoreBluetooth client
    │   ├── CSVParser.swift         # parser del formato del sketch
    │   └── MockDataProvider.swift  # genera lecturas falsas
    ├── ViewModels/
    │   └── MonitorViewModel.swift  # orquesta BLE + mock
    └── Views/
        ├── DisclaimerView.swift    # Términos, bloquea hasta aceptar
        ├── ConnectionView.swift    # escanea y conecta al ESP32
        ├── LiveMonitorView.swift   # BPM + SpO2 + gráfica IR
        ├── HistoryView.swift       # sesiones pasadas
        ├── CalibrationView.swift   # manda c/s/l/r/g al firmware
        └── SettingsView.swift
```

## Abrir y correr (rápido)

```bash
cd ios-app
open TEC4GOOD.xcodeproj
```

Con Xcode abierto:

1. Selecciona el esquema **TEC4GOOD** arriba a la izquierda.
2. Selecciona un simulador (p. ej. **iPhone 17**) o tu iPhone conectado por cable.
3. Presiona **▶︎ Run** (Cmd+R).

La app arranca en la pantalla de **Términos y Condiciones**. Acepta para entrar. Por defecto arranca en modo **Simulado** — verás lecturas falsas de BPM y SpO₂. Para datos reales, ve a la pestaña **Conexión** y cambia a **En vivo (BLE)**.

## Correr en tu iPhone físico

1. Conecta el iPhone al Mac con cable.
2. La primera vez: *Xcode → Settings → Accounts* → agrega tu Apple ID (gratis).
3. Con el proyecto abierto, selecciona *TEC4GOOD → Signing & Capabilities* y en **Team** elige tu Apple ID.
4. Selecciona tu iPhone en la barra de arriba como destino.
5. **▶︎ Run**.
6. Si sale error de "untrusted developer" en el iPhone: *Ajustes → General → VPN y gestión del dispositivo →* autoriza tu perfil.

## Regenerar el proyecto Xcode (opcional)

Si editas `project.yml` o agregas archivos nuevos:

```bash
cd ios-app
xcodegen generate
```

Esto regenera `TEC4GOOD.xcodeproj` desde cero.

## Build desde línea de comandos

```bash
# Compilar para simulador sin firmar
xcodebuild -project TEC4GOOD.xcodeproj \
  -scheme TEC4GOOD \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  -configuration Debug \
  build CODE_SIGNING_ALLOWED=NO
```

## Protocolo BLE

La app y el firmware se ponen de acuerdo por estos UUIDs. Si cambias uno, **cambia los dos**.

| Campo | UUID |
|-------|------|
| Service | `0000FEED-0000-1000-8000-00805F9B34FB` |
| DATA (notify) | `0000FEE1-0000-1000-8000-00805F9B34FB` |
| COMMAND (write) | `0000FEE2-0000-1000-8000-00805F9B34FB` |

Formato del payload en DATA (texto ASCII):

```
timestamp_ms,ir,red,bpm,spo2\n
```

Ejemplos:

```
12345,82341,61204,72.3,97.4
12445,81988,60890,72.3,97.1
```

Mensajes del firmware (no CSV) se prefijan con `#`:

```
# CALIBRACION iniciada
# Paso 1/2: dedo quieto 30s
```

En COMMAND el iPhone escribe un solo carácter:

| Cmd | Efecto |
|-----|--------|
| `c` | Inicia calibración |
| `s` | Guarda calibración en EEPROM |
| `l` | Carga calibración desde EEPROM |
| `r` | Reset a valores de fábrica |
| `g` | Toggle CSV (reservado) |
| `?` | Muestra ayuda |

## Modo demo

Si no tienes el ESP32 a la mano, en la pestaña **Conexión** selecciona **Simulado**. El `MockDataProvider` genera BPM y SpO₂ plausibles a 20 Hz para probar la UI.

En el **Monitor** puedes tocar el botón de la mano para simular "dedo retirado" y ver cómo reacciona el statusHint.

## Debugging del BLE

Si la app no ve al ESP32:

1. Confirma que el sketch está corriendo — abre Serial Monitor del Arduino IDE a 115200 baud y deberías ver "BLE advertising como 'TEC4GOOD'".
2. En el iPhone: *Ajustes → Privacidad y seguridad → Bluetooth →* asegúrate que TEC4GOOD tiene permiso.
3. Usa la app **nRF Connect** (gratis) desde otro dispositivo para verificar que el ESP32 advertiza correctamente.
4. Revisa que ambos usen los mismos UUIDs (ver arriba).

## Limitaciones actuales (MVP)

- Historial de sesiones vive solo en memoria — se pierde al cerrar la app. SQLite o SwiftData es el siguiente paso.
- No hay export de CSV.
- No hay gráfica histórica en la vista de Historial.
- La app asume que el ESP32 expone los UUIDs específicos de TEC4GOOD. No detecta HM-10 genéricos.

Roadmap en el [README raíz](../README.md#roadmap).
