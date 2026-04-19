import Foundation

/// Parsea el formato CSV que emite el sketch:
///   "timestamp_ms,ir,red,bpm,spo2"
/// Valores vacíos (por ejemplo SpO2 sin medir aún) se devuelven como nil.
enum CSVParser {

    static func parse(_ line: String) -> Reading? {
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)

        // Ignora comentarios y header del sketch
        if trimmed.isEmpty || trimmed.hasPrefix("#") { return nil }

        let parts = trimmed.split(separator: ",", omittingEmptySubsequences: false)
        guard parts.count >= 5 else { return nil }

        guard
            let ts = UInt64(parts[0]),
            let ir = UInt32(parts[1]),
            let red = UInt32(parts[2])
        else { return nil }

        let bpm = Double(parts[3])
        let spo2: Double? = parts[4].isEmpty ? nil : Double(parts[4])

        return Reading(
            receivedAt: Date(),
            timestampMs: ts,
            ir: ir,
            red: red,
            bpm: bpm.flatMap { $0 > 0 ? $0 : nil },
            spo2: spo2.flatMap { $0 > 0 ? $0 : nil }
        )
    }
}
