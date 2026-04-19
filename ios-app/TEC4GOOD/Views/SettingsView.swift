import SwiftUI

struct SettingsView: View {
    @AppStorage("acceptedTerms") private var acceptedTerms = false

    var body: some View {
        Form {
            Section("Acerca de") {
                LabeledContent("App", value: "TEC4GOOD")
                LabeledContent("Versión", value: Bundle.main.shortVersion + " (\(Bundle.main.buildNumber))")
                LabeledContent("Hardware", value: "ESP32 + MAX30102")
            }

            Section("Términos y condiciones") {
                NavigationLink("Ver términos completos") {
                    TermsFullView()
                }
                Button(role: .destructive) {
                    acceptedTerms = false
                } label: {
                    Label("Revocar aceptación", systemImage: "arrow.uturn.backward")
                }
            }

            Section {
                Text("TEC4GOOD es un proyecto **educativo**. No es un dispositivo médico. No usar para diagnóstico ni tratamiento.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Ajustes")
    }
}

struct TermsFullView: View {
    var body: some View {
        ScrollView {
            Text(termsText)
                .font(.callout)
                .padding()
        }
        .navigationTitle("Términos")
    }

    private var termsText: String {
        """
        TEC4GOOD — Términos y aviso médico (resumen)

        1. Propósito: Herramienta EDUCATIVA y de prototipado. NO es un \
        dispositivo médico.

        2. No es asesoría médica: las lecturas de pulso y SpO₂ son \
        estimaciones de un prototipo con error típico de ±3–5% o mayor. \
        No usar para diagnóstico, tratamiento ni toma de decisiones \
        clínicas.

        3. Emergencia: llame al número de emergencia de su país. Este \
        software no sustituye atención médica.

        4. Población restringida: no usar en menores sin supervisión, \
        personas con marcapasos, pacientes con condiciones crónicas, \
        ni embarazadas sin supervisión profesional.

        5. Privacidad: la app corre localmente. Las lecturas no se \
        envían a servidores externos.

        6. Responsabilidad: el uso es bajo su propio riesgo. Los \
        autores no responden por daños derivados del uso.

        Versión completa en el repositorio: TERMS_AND_CONDITIONS.md
        """
    }
}

private extension Bundle {
    var shortVersion: String { (infoDictionary?["CFBundleShortVersionString"] as? String) ?? "—" }
    var buildNumber: String  { (infoDictionary?["CFBundleVersion"] as? String) ?? "—" }
}

#Preview {
    NavigationStack { SettingsView() }
}
