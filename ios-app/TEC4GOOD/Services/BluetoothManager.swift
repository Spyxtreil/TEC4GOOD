import Foundation
import CoreBluetooth
import Combine

/// UUIDs del servicio BLE del ESP32. Deben matchear los del sketch.
enum BLEUUID {
    static let service    = CBUUID(string: "0000FEED-0000-1000-8000-00805F9B34FB")
    static let dataChar   = CBUUID(string: "0000FEE1-0000-1000-8000-00805F9B34FB")
    static let cmdChar    = CBUUID(string: "0000FEE2-0000-1000-8000-00805F9B34FB")
}

/// Estado de conexión, expuesto a la UI.
enum ConnectionState: Equatable {
    case idle
    case bluetoothOff
    case unauthorized
    case scanning
    case connecting(name: String)
    case connected(name: String)
    case disconnected(reason: String?)
    case error(String)
}

/// Gestor Bluetooth LE central. Descubre, se conecta al ESP32 TEC4GOOD,
/// se suscribe a la característica de datos y expone las lecturas.
@MainActor
final class BluetoothManager: NSObject, ObservableObject {
    @Published private(set) var state: ConnectionState = .idle
    @Published private(set) var discovered: [CBPeripheral] = []
    @Published private(set) var latestReading: Reading?
    @Published private(set) var readingsBuffer: [Reading] = []
    @Published private(set) var lastDeviceMessage: String?

    /// Máximo de lecturas que guardamos en memoria para graficar.
    var bufferLimit: Int = 300

    private var central: CBCentralManager!
    private var peripheral: CBPeripheral?
    private var dataCharacteristic: CBCharacteristic?
    private var cmdCharacteristic: CBCharacteristic?
    private var lineBuffer = ""

    override init() {
        super.init()
        central = CBCentralManager(delegate: self, queue: .main, options: [
            CBCentralManagerOptionShowPowerAlertKey: true
        ])
    }

    func startScan() {
        guard central.state == .poweredOn else {
            state = (central.state == .poweredOff) ? .bluetoothOff : .error("Bluetooth no disponible")
            return
        }
        discovered.removeAll()
        state = .scanning
        central.scanForPeripherals(withServices: [BLEUUID.service], options: [
            CBCentralManagerScanOptionAllowDuplicatesKey: false
        ])
    }

    func stopScan() {
        central.stopScan()
        if case .scanning = state { state = .idle }
    }

    func connect(_ p: CBPeripheral) {
        stopScan()
        peripheral = p
        peripheral?.delegate = self
        state = .connecting(name: p.name ?? "ESP32")
        central.connect(p, options: nil)
    }

    func disconnect() {
        if let p = peripheral {
            central.cancelPeripheralConnection(p)
        }
    }

    func send(_ command: DeviceCommand) {
        guard
            let p = peripheral,
            let c = cmdCharacteristic,
            let data = command.rawValue.data(using: .utf8)
        else { return }
        p.writeValue(data, for: c, type: .withResponse)
    }

    func clearBuffer() {
        readingsBuffer.removeAll()
    }

    // MARK: - Helpers

    private func ingestIncoming(_ chunk: String) {
        // Concatena chunks, parsea líneas completas.
        lineBuffer += chunk
        while let rangeOfNewline = lineBuffer.firstIndex(where: { $0 == "\n" || $0 == "\r" }) {
            let line = String(lineBuffer[..<rangeOfNewline])
            lineBuffer.removeSubrange(...rangeOfNewline)

            if line.hasPrefix("#") {
                lastDeviceMessage = String(line.dropFirst()).trimmingCharacters(in: .whitespaces)
                continue
            }

            if let reading = CSVParser.parse(line) {
                latestReading = reading
                readingsBuffer.append(reading)
                if readingsBuffer.count > bufferLimit {
                    readingsBuffer.removeFirst(readingsBuffer.count - bufferLimit)
                }
            } else if !line.isEmpty {
                lastDeviceMessage = line.trimmingCharacters(in: .whitespaces)
            }
        }
    }
}

// MARK: - CBCentralManagerDelegate

extension BluetoothManager: CBCentralManagerDelegate {
    nonisolated func centralManagerDidUpdateState(_ central: CBCentralManager) {
        Task { @MainActor in
            switch central.state {
            case .poweredOn:       self.state = .idle
            case .poweredOff:      self.state = .bluetoothOff
            case .unauthorized:    self.state = .unauthorized
            case .unsupported:     self.state = .error("Este dispositivo no soporta BLE")
            case .resetting:       self.state = .error("Bluetooth reiniciándose…")
            case .unknown:         self.state = .idle
            @unknown default:      self.state = .error("Estado BLE desconocido")
            }
        }
    }

    nonisolated func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String : Any],
        rssi RSSI: NSNumber
    ) {
        Task { @MainActor in
            if !self.discovered.contains(where: { $0.identifier == peripheral.identifier }) {
                self.discovered.append(peripheral)
            }
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        Task { @MainActor in
            self.state = .connected(name: peripheral.name ?? "ESP32")
            peripheral.discoverServices([BLEUUID.service])
        }
    }

    nonisolated func centralManager(
        _ central: CBCentralManager,
        didDisconnectPeripheral peripheral: CBPeripheral,
        error: Error?
    ) {
        Task { @MainActor in
            self.dataCharacteristic = nil
            self.cmdCharacteristic = nil
            self.state = .disconnected(reason: error?.localizedDescription)
        }
    }

    nonisolated func centralManager(
        _ central: CBCentralManager,
        didFailToConnect peripheral: CBPeripheral,
        error: Error?
    ) {
        Task { @MainActor in
            self.state = .error(error?.localizedDescription ?? "No se pudo conectar")
        }
    }
}

// MARK: - CBPeripheralDelegate

extension BluetoothManager: CBPeripheralDelegate {
    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let svc = peripheral.services?.first(where: { $0.uuid == BLEUUID.service }) else { return }
        peripheral.discoverCharacteristics([BLEUUID.dataChar, BLEUUID.cmdChar], for: svc)
    }

    nonisolated func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        for c in service.characteristics ?? [] {
            if c.uuid == BLEUUID.dataChar {
                peripheral.setNotifyValue(true, for: c)
                Task { @MainActor in self.dataCharacteristic = c }
            } else if c.uuid == BLEUUID.cmdChar {
                Task { @MainActor in self.cmdCharacteristic = c }
            }
        }
    }

    nonisolated func peripheral(
        _ peripheral: CBPeripheral,
        didUpdateValueFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        guard
            characteristic.uuid == BLEUUID.dataChar,
            let data = characteristic.value,
            let str = String(data: data, encoding: .utf8)
        else { return }
        Task { @MainActor in
            self.ingestIncoming(str)
        }
    }
}
