import SwiftUI

struct CalibrationView: View {
    @EnvironmentObject var vm: MonitorViewModel
    @State private var showConfirmReset = false

    var body: some View {
        Form {
            Section("Comandos del dispositivo") {
                commandButton(
                    "Iniciar calibración",
                    systemImage: "target",
                    cmd: .startCalibration,
                    color: .blue,
                    help: "Rutina de 60 s. Sigue las instrucciones en el monitor del dispositivo."
                )
                commandButton(
                    "Guardar en EEPROM",
                    systemImage: "internaldrive",
                    cmd: .saveCalibration,
                    color: .green,
                    help: "Persiste la calibración actual para que sobreviva reinicios."
                )
                commandButton(
                    "Cargar desde EEPROM",
                    systemImage: "arrow.down.doc",
                    cmd: .loadCalibration,
                    color: .orange,
                    help: "Recupera la última calibración guardada."
                )
                commandButton(
                    "Reiniciar a fábrica",
                    systemImage: "arrow.counterclockwise",
                    cmd: .resetCalibration,
                    color: .red,
                    help: "Vuelve a valores por defecto (sin calibrar)."
                )
                commandButton(
                    "Toggle log CSV",
                    systemImage: "doc.plaintext",
                    cmd: .toggleCSV,
                    color: .purple,
                    help: "Activa/desactiva el stream crudo de datos."
                )
            }

            Section("Estado") {
                if vm.dataSource != .live {
                    Label(
                        "Cambia a modo 'En vivo' en Conexión para mandar comandos.",
                        systemImage: "info.circle"
                    )
                    .foregroundStyle(.secondary)
                    .font(.footnote)
                } else if case .connected = vm.ble.state {
                    Label("Listo para enviar comandos", systemImage: "checkmark.circle")
                        .foregroundStyle(.green)
                } else {
                    Label("Conéctate al ESP32 primero", systemImage: "exclamationmark.circle")
                        .foregroundStyle(.orange)
                }
            }
        }
        .navigationTitle("Calibración")
    }

    private func commandButton(
        _ title: String,
        systemImage: String,
        cmd: DeviceCommand,
        color: Color,
        help: String
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Button {
                vm.ble.send(cmd)
            } label: {
                Label(title, systemImage: systemImage)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .foregroundStyle(color)
            }
            .disabled(!canSend)
            Text(help)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    private var canSend: Bool {
        if vm.dataSource != .live { return false }
        if case .connected = vm.ble.state { return true }
        return false
    }
}

#Preview {
    NavigationStack {
        CalibrationView().environmentObject(MonitorViewModel())
    }
}
