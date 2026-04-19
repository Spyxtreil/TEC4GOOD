import Foundation

/// Estado de calibración del sensor (mirror de la struct `Calib` en el sketch).
/// La app no calcula calibración por sí misma — solo manda comandos
/// al ESP32 y muestra lo que el firmware reporta.
struct CalibrationState: Hashable {
    var spo2A: Double
    var spo2B: Double
    var fingerThreshold: UInt32
    var calibrated: Bool

    static let factory = CalibrationState(
        spo2A: 110.0,
        spo2B: 25.0,
        fingerThreshold: 50_000,
        calibrated: false
    )
}

/// Comandos que la app puede mandar al ESP32 via la característica
/// COMMAND. Matchean uno-a-uno con los del monitor serie del sketch.
enum DeviceCommand: String {
    case startCalibration   = "c"
    case saveCalibration    = "s"
    case loadCalibration    = "l"
    case resetCalibration   = "r"
    case toggleCSV          = "g"
    case help               = "?"
}
