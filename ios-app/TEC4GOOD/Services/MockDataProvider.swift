import Foundation
import Combine

/// Genera lecturas simuladas para presentaciones sin hardware.
/// Publica una Reading nueva cada ~50 ms con BPM y SpO2 plausibles.
@MainActor
final class MockDataProvider: ObservableObject {
    @Published var latestReading: Reading?
    @Published var readingsBuffer: [Reading] = []

    var bufferLimit: Int = 300
    private var timer: Timer?
    private var phase: Double = 0
    private var startMs: UInt64 = 0
    private var hasFinger: Bool = true

    func start() {
        stop()
        startMs = UInt64(Date().timeIntervalSince1970 * 1000)
        timer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    func toggleFinger() { hasFinger.toggle() }

    private func tick() {
        phase += 0.05
        let baseBPM = 72.0 + 6.0 * sin(phase * 0.2)                // 66–78
        let noise = Double.random(in: -1.5...1.5)
        let bpm = baseBPM + noise
        let spo2 = 97.0 + Double.random(in: -0.8...0.8)

        // IR/red simulando pulsación: onda + DC
        let pulse = sin(phase * (2 * .pi * bpm / 60.0))            // Hz aprox
        let ir: UInt32 = hasFinger ? UInt32(80_000 + pulse * 8_000 + Double.random(in: -500...500))
                                   : UInt32(Double.random(in: 5_000...12_000))
        let red: UInt32 = hasFinger ? UInt32(60_000 + pulse * 5_500 + Double.random(in: -400...400))
                                    : UInt32(Double.random(in: 3_000...9_000))

        let r = Reading(
            receivedAt: Date(),
            timestampMs: UInt64(Date().timeIntervalSince1970 * 1000) - startMs,
            ir: ir,
            red: red,
            bpm: hasFinger ? bpm : nil,
            spo2: hasFinger ? spo2 : nil
        )
        latestReading = r
        readingsBuffer.append(r)
        if readingsBuffer.count > bufferLimit {
            readingsBuffer.removeFirst(readingsBuffer.count - bufferLimit)
        }
    }

    func clearBuffer() {
        readingsBuffer.removeAll()
    }
}
