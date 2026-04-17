# Términos, Condiciones y Aviso Médico

**Última actualización:** 2026-04-17
**Proyecto:** TEC4GOOD — Herramientas de bienestar (ADHD Activity Planner, Nutrition Advisor, Arduino Oximeter)

---

## 1. Aceptación

Al usar cualquiera de los programas, scripts, sketches o firmware contenidos en este repositorio ("el Software"), usted declara haber leído, entendido y aceptado estos Términos y Condiciones. Si no está de acuerdo, no utilice el Software.

## 2. Propósito del Software

El Software se distribuye con fines **educativos, informativos y de prototipado**. Fue creado como proyecto estudiantil/académico y no está certificado, registrado ni aprobado por ningún organismo regulador sanitario (COFEPRIS, FDA, CE, ISO 13485, etc.).

## 3. No constituye asesoría médica

**IMPORTANTE — LEA CON ATENCIÓN.**

Las recomendaciones, planes, cálculos, umbrales y lecturas producidos por este Software (incluyendo pero no limitado a: pasos diarios sugeridos, subtipo ADHD, actividades físicas, calorías, macronutrientes, IMC, BMR, TDEE, frecuencia cardiaca, saturación de oxígeno, clasificaciones "normal/taquicardia/bradicardia/SpO2 baja") **NO constituyen diagnóstico, tratamiento, prescripción ni asesoría médica profesional**.

- Consulte siempre a un médico, dietista registrado, psicólogo o profesional de la salud certificado antes de:
  - Iniciar un plan de ejercicio.
  - Modificar su dieta o ingesta calórica.
  - Tomar decisiones clínicas basadas en lecturas del sensor.
  - Interpretar sus propios signos vitales.
- **En caso de emergencia médica, llame inmediatamente al número de emergencias de su país** (911 en México, 112 en UE, 911 en EE.UU.). No utilice este Software como sustituto de atención médica.

## 4. Limitaciones del hardware (MAX30102 / Arduino)

El sketch Arduino incluido utiliza el módulo **MAX30102** en una configuración de prototipo casero. Este dispositivo **NO es un oxímetro de pulso médico** y:

- No está calibrado contra referencias clínicas.
- La fórmula de SpO₂ empleada es una aproximación empírica con error típico de ±3-5 % o mayor.
- La detección de latidos puede fallar por movimiento, luz ambiente, presión inadecuada del dedo, o pigmentación de piel.
- No debe usarse para monitoreo médico, diagnóstico, ni toma de decisiones clínicas.
- No debe usarse en pacientes, menores, personas con condiciones cardiacas, respiratorias o neurológicas sin supervisión profesional.

## 5. Limitaciones del software de ADHD y nutrición

- Las categorías, puntajes de "impulse control", recomendaciones de actividad y planes nutricionales se basan en heurísticas generales de literatura pública y **no son evaluaciones clínicas**.
- El IMC es una métrica poblacional con limitaciones conocidas (no distingue masa muscular, edad avanzada, embarazo, etc.).
- Las fórmulas Mifflin-St Jeor y los factores de actividad son estimaciones; el metabolismo real varía ±10-20 %.
- El Software no considera: alergias alimentarias, intolerancias, enfermedades crónicas (diabetes, hipertensión, enfermedad renal, trastornos alimentarios), embarazo, lactancia, medicamentos, ni contraindicaciones individuales.

## 6. Exención de responsabilidad

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A GARANTÍAS DE COMERCIABILIDAD, IDONEIDAD PARA UN PROPÓSITO PARTICULAR, PRECISIÓN, O NO INFRACCIÓN.

EN NINGÚN CASO LOS AUTORES, COLABORADORES NI MANTENEDORES SERÁN RESPONSABLES POR:
- Daños directos, indirectos, incidentales, especiales, ejemplares o consecuentes.
- Pérdida de salud, lesiones, daños físicos o psicológicos.
- Decisiones tomadas con base en los resultados del Software.
- Mal funcionamiento del hardware, electrocuciones, quemaduras o incendios por cableado incorrecto.
- Pérdida de datos, tiempo o dinero.

El uso del Software es **bajo su propio riesgo y responsabilidad**.

## 7. Privacidad y datos

El Software se ejecuta **localmente** y **no recolecta, transmite ni almacena datos personales** fuera de su dispositivo. Los valores que ingrese (edad, peso, altura, subtipo ADHD, etc.) permanecen en la sesión de ejecución y se pierden al cerrarla, salvo que usted decida guardarlos manualmente. Usted es responsable de proteger cualquier archivo de salida que genere.

## 8. Uso apropiado

Usted se compromete a:
- No usar el Software en contextos clínicos, hospitalarios o de atención a terceros sin consentimiento informado y supervisión profesional.
- No representar las salidas del Software como opiniones médicas profesionales.
- No modificar el Software para eliminar los avisos de seguridad antes de redistribuirlo.
- Respetar las licencias de las librerías de terceros (SparkFun MAX3010x, etc.).

## 9. Seguridad eléctrica (hardware)

- Use siempre la alimentación correcta indicada en la documentación (3.3 V para el MAX30102).
- Verifique el cableado **antes** de conectar el USB.
- No opere el circuito en ambientes húmedos ni con las manos mojadas.
- Desconecte la alimentación antes de modificar conexiones.
- En caso de olor, humo o calor anormal, desconecte inmediatamente.

## 10. Población restringida

Este Software **no** debe ser utilizado por, o para:
- Menores de 18 años sin supervisión de un adulto responsable.
- Personas con marcapasos u otros dispositivos médicos implantados (riesgo por LEDs y corrientes del sensor en contacto prolongado).
- Personas con trastornos alimentarios activos o en tratamiento, sin supervisión de su equipo clínico.
- Diagnóstico o seguimiento de cualquier condición médica.

## 11. Modificaciones

Estos Términos pueden actualizarse. La versión vigente es siempre la presente en el repositorio. El uso continuado del Software tras una actualización constituye aceptación de los nuevos Términos.

## 12. Legislación aplicable

Estos Términos se rigen por la legislación del lugar de residencia del autor principal, sin perjuicio de las normas imperativas de protección al consumidor que pudieran aplicar en su jurisdicción.

## 13. Contacto

Para reportar bugs, vulnerabilidades o dudas sobre estos Términos, abra un *issue* en el repositorio.

---

**AL EJECUTAR CUALQUIERA DE LOS PROGRAMAS DEL REPOSITORIO, USTED CONFIRMA QUE HA LEÍDO Y ACEPTA ESTOS TÉRMINOS.**
