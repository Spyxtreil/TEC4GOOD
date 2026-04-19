import SwiftUI
import Charts

struct LiveMonitorView: View {
    @EnvironmentObject var vm: MonitorViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                statusBanner
                metricsGrid
                signalChart
                controls
                disclaimer
            }
            .padding()
        }
        .navigationTitle("Monitor")
        .onAppear {
            // Arranca mock si ese es el modo.
            if vm.dataSource == .mock { vm.mock.start() }
        }
    }

    // MARK: - Subviews

    private var statusBanner: some View {
        HStack {
            Circle()
                .fill(hasLive ? Color.green : Color.gray)
                .frame(width: 10, height: 10)
            Text(hasLive ? "Recibiendo datos" : "Sin datos")
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
            Text(vm.dataSource == .mock ? "MODO DEMO" : "EN VIVO")
                .font(.caption2.bold())
                .padding(.horizontal, 8).padding(.vertical, 3)
                .background(
                    (vm.dataSource == .mock ? Color.orange : Color.green)
                        .opacity(0.15)
                )
                .clipShape(Capsule())
        }
    }

    private var metricsGrid: some View {
        HStack(spacing: 12) {
            metricCard(
                title: "BPM",
                value: vm.latest?.bpm.map { String(format: "%.0f", $0) } ?? "--",
                unit: "lpm",
                icon: "heart.fill",
                color: .red
            )
            metricCard(
                title: "SpO₂",
                value: vm.latest?.spo2.map { String(format: "%.1f", $0) } ?? "--",
                unit: "%",
                icon: "lungs.fill",
                color: .blue
            )
        }
    }

    private func metricCard(title: String, value: String, unit: String, icon: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Label(title, systemImage: icon)
                .font(.caption)
                .foregroundStyle(color)
            HStack(alignment: .lastTextBaseline, spacing: 4) {
                Text(value)
                    .font(.system(size: 42, weight: .semibold, design: .rounded))
                    .contentTransition(.numericText())
                Text(unit).font(.caption).foregroundStyle(.secondary)
            }
            if let s = vm.latest?.statusHint {
                Text(s.rawValue)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private var signalChart: some View {
        let window = Array(vm.readings.suffix(200))
        return VStack(alignment: .leading) {
            Text("Señal IR (últimas lecturas)")
                .font(.caption)
                .foregroundStyle(.secondary)
            Chart(window) { r in
                LineMark(
                    x: .value("t", r.receivedAt),
                    y: .value("IR", Double(r.ir))
                )
                .foregroundStyle(.red.gradient)
                .interpolationMethod(.catmullRom)
            }
            .chartYAxis(.hidden)
            .chartXAxis(.hidden)
            .frame(height: 140)
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    private var controls: some View {
        HStack {
            if vm.currentSession == nil {
                Button {
                    vm.startSession()
                } label: {
                    Label("Iniciar sesión", systemImage: "record.circle")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            } else {
                Button(role: .destructive) {
                    vm.endSession()
                } label: {
                    Label("Terminar sesión", systemImage: "stop.circle")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }

            if vm.dataSource == .mock {
                Button {
                    vm.mock.toggleFinger()
                } label: {
                    Image(systemName: "hand.point.up.left.fill")
                }
                .buttonStyle(.bordered)
            }
        }
    }

    private var disclaimer: some View {
        Text("Estas lecturas son una estimación. **NO son diagnóstico médico.**")
            .font(.caption2)
            .foregroundStyle(.secondary)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity)
            .padding(.top, 8)
    }

    private var hasLive: Bool {
        guard let last = vm.latest else { return false }
        return Date().timeIntervalSince(last.receivedAt) < 2.5
    }
}

#Preview {
    NavigationStack {
        LiveMonitorView()
            .environmentObject({
                let m = MonitorViewModel()
                m.dataSource = .mock
                m.mock.start()
                return m
            }())
    }
}
