import SwiftUI
import CoreBluetooth

struct ConnectionView: View {
    @EnvironmentObject var vm: MonitorViewModel

    var body: some View {
        Form {
            Section("Fuente de datos") {
                Picker("Modo", selection: $vm.dataSource) {
                    Text("Simulado").tag(DataSource.mock)
                    Text("En vivo (BLE)").tag(DataSource.live)
                }
                .pickerStyle(.segmented)

                if vm.dataSource == .mock {
                    Label(
                        "Los datos son generados localmente para demo. " +
                        "Cambia a 'En vivo' cuando el ESP32 esté encendido.",
                        systemImage: "info.circle"
                    )
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                }
            }

            if vm.dataSource == .live {
                Section("Estado") {
                    statusRow
                }

                Section {
                    if case .scanning = vm.ble.state {
                        Button("Detener búsqueda", role: .destructive) {
                            vm.ble.stopScan()
                        }
                    } else if case .connected = vm.ble.state {
                        Button("Desconectar", role: .destructive) {
                            vm.ble.disconnect()
                        }
                    } else {
                        Button {
                            vm.ble.startScan()
                        } label: {
                            Label("Buscar dispositivos TEC4GOOD", systemImage: "magnifyingglass")
                        }
                    }
                }

                if !vm.ble.discovered.isEmpty {
                    Section("Dispositivos encontrados") {
                        ForEach(vm.ble.discovered, id: \.identifier) { p in
                            Button {
                                vm.ble.connect(p)
                            } label: {
                                HStack {
                                    Image(systemName: "dot.radiowaves.left.and.right")
                                    VStack(alignment: .leading) {
                                        Text(p.name ?? "Desconocido")
                                        Text(p.identifier.uuidString)
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                }
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                if let msg = vm.ble.lastDeviceMessage {
                    Section("Último mensaje del dispositivo") {
                        Text(msg).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Conexión")
    }

    @ViewBuilder
    private var statusRow: some View {
        switch vm.ble.state {
        case .idle:
            Label("Listo para buscar", systemImage: "circle")
        case .bluetoothOff:
            Label("Activa el Bluetooth en Ajustes", systemImage: "xmark.circle").foregroundStyle(.red)
        case .unauthorized:
            Label("Permite el acceso a Bluetooth en Ajustes", systemImage: "lock").foregroundStyle(.orange)
        case .scanning:
            Label("Buscando…", systemImage: "antenna.radiowaves.left.and.right")
        case .connecting(let name):
            Label("Conectando a \(name)…", systemImage: "arrow.triangle.2.circlepath")
        case .connected(let name):
            Label("Conectado a \(name)", systemImage: "checkmark.circle.fill").foregroundStyle(.green)
        case .disconnected(let reason):
            Label(reason ?? "Desconectado", systemImage: "bolt.slash").foregroundStyle(.orange)
        case .error(let msg):
            Label(msg, systemImage: "exclamationmark.triangle").foregroundStyle(.red)
        }
    }
}

#Preview {
    NavigationStack {
        ConnectionView()
            .environmentObject(MonitorViewModel())
    }
}
