import Foundation
import Combine
import SwiftUI

/// Modo de operación de la app: datos reales por BLE o simulados.
enum DataSource: Equatable {
    case live
    case mock
}

/// Orquesta BluetoothManager y MockDataProvider para la UI.
/// La UI solo observa este ViewModel.
@MainActor
final class MonitorViewModel: ObservableObject {
    @Published var dataSource: DataSource = .mock {
        didSet { switchSource() }
    }

    // Proveedores
    @Published var ble = BluetoothManager()
    @Published var mock = MockDataProvider()

    // Estado de la sesión activa
    @Published var currentSession: Session?
    @Published var sessions: [Session] = []

    // Buffer y lectura actual expuestos a la UI según el modo.
    var readings: [Reading] {
        dataSource == .mock ? mock.readingsBuffer : ble.readingsBuffer
    }

    var latest: Reading? {
        dataSource == .mock ? mock.latestReading : ble.latestReading
    }

    private var cancellables = Set<AnyCancellable>()

    init() {
        // Cuando hay nueva lectura, agrégala a la sesión activa si hay una.
        mock.$latestReading
            .compactMap { $0 }
            .sink { [weak self] r in self?.appendToSessionIfActive(r) }
            .store(in: &cancellables)
        ble.$latestReading
            .compactMap { $0 }
            .sink { [weak self] r in self?.appendToSessionIfActive(r) }
            .store(in: &cancellables)
    }

    private func switchSource() {
        switch dataSource {
        case .mock:
            ble.disconnect()
            mock.start()
        case .live:
            mock.stop()
        }
    }

    func startSession() {
        currentSession = Session()
    }

    func endSession() {
        guard var s = currentSession else { return }
        s.endedAt = Date()
        sessions.insert(s, at: 0)
        currentSession = nil
    }

    private func appendToSessionIfActive(_ r: Reading) {
        guard currentSession != nil else { return }
        currentSession?.readings.append(r)
    }
}
