import Foundation

/// Una sesión de monitoreo — inicio, fin, y la lista de lecturas en medio.
struct Session: Identifiable, Hashable {
    let id: UUID
    let startedAt: Date
    var endedAt: Date?
    var readings: [Reading]

    init(id: UUID = UUID(), startedAt: Date = Date(), readings: [Reading] = []) {
        self.id = id
        self.startedAt = startedAt
        self.readings = readings
    }

    var duration: TimeInterval {
        guard let end = endedAt else { return Date().timeIntervalSince(startedAt) }
        return end.timeIntervalSince(startedAt)
    }

    var avgBPM: Double? {
        let values = readings.compactMap(\.bpm).filter { $0 > 20 && $0 < 255 }
        guard !values.isEmpty else { return nil }
        return values.reduce(0, +) / Double(values.count)
    }

    var avgSpO2: Double? {
        let values = readings.compactMap(\.spo2).filter { $0 > 70 && $0 <= 100 }
        guard !values.isEmpty else { return nil }
        return values.reduce(0, +) / Double(values.count)
    }
}
