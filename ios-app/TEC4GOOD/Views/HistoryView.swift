import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var vm: MonitorViewModel

    var body: some View {
        List {
            if vm.sessions.isEmpty {
                ContentUnavailableView(
                    "Sin sesiones",
                    systemImage: "clock.arrow.circlepath",
                    description: Text("Inicia una sesión en la pestaña Monitor para empezar a guardar lecturas.")
                )
            } else {
                ForEach(vm.sessions) { s in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(s.startedAt, format: .dateTime.day().month().hour().minute())
                            .font(.headline)
                        HStack(spacing: 16) {
                            Label(
                                s.avgBPM.map { String(format: "%.0f lpm", $0) } ?? "— lpm",
                                systemImage: "heart.fill"
                            )
                            Label(
                                s.avgSpO2.map { String(format: "%.1f%%", $0) } ?? "—%",
                                systemImage: "lungs.fill"
                            )
                            Label(
                                String(format: "%.0fs", s.duration),
                                systemImage: "clock"
                            )
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        Text("\(s.readings.count) lecturas")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .navigationTitle("Historial")
    }
}

#Preview {
    NavigationStack {
        HistoryView().environmentObject(MonitorViewModel())
    }
}
