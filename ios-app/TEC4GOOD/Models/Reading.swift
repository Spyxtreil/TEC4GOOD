import Foundation

/// Una lectura instantánea del sensor MAX30102.
/// Llega por BLE desde el ESP32 como un paquete CSV:
///   "timestamp_ms,ir,red,bpm,spo2"
struct Reading: Identifiable, Hashable {
    let id = UUID()
    let receivedAt: Date
    let timestampMs: UInt64
    let ir: UInt32
    let red: UInt32
    let bpm: Double?
    let spo2: Double?

    var hasFinger: Bool { ir > 20_000 }

    /// Evaluación sin diagnóstico. Las etiquetas son descriptivas,
    /// NO son interpretación médica. Siempre llevar "[NO DIAGNÓSTICO]"
    /// cerca en la UI.
    enum StatusHint: String {
        case noFinger = "Sin dedo"
        case lowSpO2 = "SpO₂ baja"
        case highRate = "Frecuencia alta"
        case lowRate = "Frecuencia baja"
        case normal = "Dentro de rango"
    }

    var statusHint: StatusHint {
        if !hasFinger { return .noFinger }
        if let s = spo2, s > 0, s < 94 { return .lowSpO2 }
        if let b = bpm, b > 100 { return .highRate }
        if let b = bpm, b > 0, b < 50 { return .lowRate }
        return .normal
    }
}
