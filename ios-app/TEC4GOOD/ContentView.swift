import SwiftUI

struct ContentView: View {
    @AppStorage("acceptedTerms") private var acceptedTerms = false
    @StateObject private var vm = MonitorViewModel()

    var body: some View {
        if !acceptedTerms {
            DisclaimerView(accepted: $acceptedTerms)
        } else {
            TabView {
                NavigationStack { LiveMonitorView() }
                    .tabItem { Label("Monitor", systemImage: "waveform.path.ecg") }

                NavigationStack { ConnectionView() }
                    .tabItem { Label("Conexión", systemImage: "antenna.radiowaves.left.and.right") }

                NavigationStack { CalibrationView() }
                    .tabItem { Label("Calibración", systemImage: "target") }

                NavigationStack { HistoryView() }
                    .tabItem { Label("Historial", systemImage: "clock.arrow.circlepath") }

                NavigationStack { SettingsView() }
                    .tabItem { Label("Ajustes", systemImage: "gearshape") }
            }
            .environmentObject(vm)
        }
    }
}

#Preview {
    ContentView()
}
