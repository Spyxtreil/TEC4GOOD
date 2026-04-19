import SwiftUI

struct DisclaimerView: View {
    @Binding var accepted: Bool
    @State private var agreed = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Label("Aviso importante", systemImage: "exclamationmark.triangle.fill")
                        .font(.title2.bold())
                        .foregroundStyle(.orange)

                    Text(
                        "TEC4GOOD es una herramienta **educativa y de prototipado**. " +
                        "No es un dispositivo médico, no está certificado clínicamente " +
                        "y las lecturas que muestra **no deben usarse para diagnóstico, " +
                        "tratamiento ni toma de decisiones clínicas**."
                    )

                    Text(
                        "El hardware (Arduino + MAX30102) es de uso experimental. " +
                        "La precisión puede variar ±3-5 % o más dependiendo de " +
                        "condiciones de uso. No lo utilice en personas con condiciones " +
                        "cardíacas, respiratorias o neurológicas sin supervisión profesional."
                    )

                    Text(
                        "En caso de emergencia médica, llame al número de emergencias " +
                        "de su país. Consulte a un profesional de la salud antes de " +
                        "interpretar cualquier medición."
                    )

                    Text("Al continuar usted acepta los Términos y Condiciones completos del proyecto.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)

                    Toggle(isOn: $agreed) {
                        Text("He leído y acepto los términos.")
                    }
                    .tint(.accentColor)

                    Button {
                        accepted = true
                    } label: {
                        Text("Continuar")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(!agreed)
                }
                .padding()
            }
            .navigationTitle("TEC4GOOD")
        }
    }
}

#Preview {
    DisclaimerView(accepted: .constant(false))
}
