# Benchmark KineIA — Dataset de Evaluación OSCE

> **Estado actual**: 15 pares pregunta-respuesta completos y ejecutables por `scripts/evaluate.py`.
>
> **Objetivo futuro**: Superar los 200 pares completos. El banco por área al final de este documento es una hoja de ruta, no un dataset terminado.
>
> **Metodología actual**: Cada entrada completa incluye una respuesta esperada y referencias de la base de conocimiento de KineIA. Este documento no acredita todavía validación clínica externa ni métricas de recuperación.

## Estado del dataset

| Estado | Cantidad |
|---|---:|
| Pares completos y ejecutables | 15 |
| Espacios pendientes en la hoja de ruta actual | 175 |
| Capacidad total definida por la hoja de ruta | 190 |
| Objetivo de largo plazo | 200+ |

Para alcanzar el objetivo de 200+, además de completar los 175 espacios pendientes, se deben definir al menos 10 entradas adicionales.

## Estructura de cada pregunta

Cada entrada del benchmark sigue este formato:

```markdown
### Pregunta #XXX
**Área**: [Traumatología / Neurología / Respiratorio / Deporte / UCI / Pediatría / Columna]
**Tema**: [Tema específico dentro del área]
**Dificultad**: [Básico / Intermedio / Avanzado]
**Modo**: [Estudiante / Profesional]
**Pregunta**: [Enunciado de la pregunta en español]
**Respuesta esperada**: [Respuesta detallada con referencias a fuentes específicas de la base de conocimiento]
**Fuentes de referencia**: [Lista de documentos en knowledge_base/ que cubren el tema]
**Ejes OSCE a evaluar**: [Lista de ejes primarios y secundarios relevantes para esta pregunta]
**Notas para el evaluador**: [Qué buscar en la respuesta, errores comunes, criterios de aceptación]
```

---

## Preguntas completas (15 — 3 por área principal)

A continuación se presentan las únicas 15 preguntas completamente desarrolladas del baseline actual. Los temas del banco por área todavía no cuentan como pares evaluables hasta incorporar todos los campos de la plantilla.

---

### ÁREA: TRAUMATOLOGÍA

---

### Pregunta #001
**Área**: Traumatología
**Tema**: Rehabilitación post-reconstrucción de LCA
**Dificultad**: Intermedio
**Modo**: Profesional
**Pregunta**: ¿Cuáles son las fases de rehabilitación post operatoria de LCA con injerto de isquiotibiales y cuáles son los objetivos principales de cada fase?
**Respuesta esperada**:
La rehabilitación post-reconstrucción de LCA se divide en 4 fases:

**Fase I — Postoperatorio Inmediato (Semana 0-2)**:
- Objetivos: Control del dolor e inflamación (crioterapia 20 min c/2h), extensión completa (0°), flexión ≥90°, activación del cuádriceps, marcha con muletas y rodillera bloqueada en extensión.
- Intervenciones clave: Movilización de rótula, extensión pasiva con toalla bajo tobillo, isométricos de cuádriceps, SLR en 4 planos.
- Precaución con injerto de isquiotibiales: No forzar isométricos de isquiotibiales en semana 0-1.

**Fase II — Fortalecimiento Temprano (Semana 2-6)**:
- Objetivos: ROM completo 0-120°, marcha independiente sin muletas, fuerza ≥3/5 (Daniels).
- Progresión: Cadena cinética cerrada inicial, sentadillas parciales (0-45°), prensa bilateral.

**Fase III — Fortalecimiento Avanzado (Semana 6-12)**:
- Objetivos: Fuerza ≥4/5, inicio de trote recto, propiocepción avanzada.
- Intervenciones: Ejercicios pliométricos de bajo impacto, desplazamientos laterales, inicio de saltos controlados.

**Fase IV — Retorno Deportivo (Semana 12-24+)**:
- Objetivos: Fuerza ≥5/5, test isocinético >85% del lado sano, single leg hop >90%.
- Criterios de return to play: Sin dolor, ROM completo, fuerza simétrica, test funcionales superados.

En todas las fases debe evitarse el ejercicio en cadena cinética abierta para cuádriceps entre 0-30° de flexión durante las primeras 12 semanas por estrés sobre el injerto.

**Fuentes de referencia**:
- `knowledge_base/protocolos/protocolo-lca-rehabilitacion.md`
- `knowledge_base/protocolos/protocolo-lca.md`
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`
- `knowledge_base/libros/biomecanica-kapandji.md`

**Ejes OSCE a evaluar**:
- Primarios: M1 (adherencia a protocolos), M4 (progresión de cargas), M8 (criterios de alta), D3 (razonamiento basado en evidencia)
- Secundarios: H1, D4, C3, C4, K1, K2

**Notas para el evaluador**: Verificar que KineIA mencione explícitamente las precauciones con injerto de isquiotibiales (no forzar flexores en fase I). El agente debe citar el protocolo específico del knowledge_base. Error común: confundir fases de LCA con fases de rehabilitación de columna.

---

### Pregunta #002
**Área**: Traumatología
**Tema**: Fractura de cadera en adulto mayor
**Dificultad**: Avanzado
**Modo**: Profesional
**Pregunta**: Según el protocolo CISFraCAM 2021, ¿cuáles son los objetivos kinésicos en las primeras 48 horas post operatorias de fractura de cadera en un paciente de 78 años con prótesis parcial de cadera?
**Respuesta esperada**:
Según los lineamientos del Consenso Intersocietario de Fractura de Cadera en el Adulto Mayor (CISFraCAM 2021), los objetivos en las primeras 48 horas son:

1. **Movilización precoz (<24 horas post-Qx)**: Sedestación al borde de la cama dentro de las primeras 24 horas. Bipedestación asistida dentro de las 48 horas.
2. **Prevención de complicaciones respiratorias**: Ejercicios de respiración diafragmática, espirometría de incentivo (Inspiron), tos asistida.
3. **Prevención de TVP**: Bombeo de tobillo bilateral cada hora, medias de compresión graduada, movilización pasiva/activa de miembros inferiores.
4. **Manejo del dolor**: EVA <4 para permitir movilización. Crioterapia local 15-20 min.
5. **Precauciones post prótesis parcial**: Evitar flexión de cadera >90°, aducción, rotación interna (riesgo de luxación). Cuña de abducción en decúbito supino.
6. **Transferencias**: Entrenamiento de cama-silla y silla-inodoro con restricciones de cadera.
7. **Fortalecimiento**: Isométricos de cuádriceps y glúteo mayor sin vencer gravedad inicialmente.

**Fuentes de referencia**:
- `knowledge_base/protocolos/protocolo-fractura-cadera.md`
- `knowledge_base/guias-clinicas/guia-kinesiologia-geriatrica.md`
- `knowledge_base/libros/traumatologia-hoppenfeld-murthy.md`
- `knowledge_base/libros/rehabilitacion-hoppenfeld.md`

**Ejes OSCE a evaluar**:
- Primarios: M1, M2 (seguridad del paciente), M4, H5 (contextualización del paciente)
- Secundarios: H4 (red flags), D6, D7, C4, K3 (contexto argentino — CISFraCAM es argentino)

**Notas para el evaluador**: FUNDAMENTAL que mencione las precauciones posturales (flexión >90°, aducción, rotación interna). Si KineIA omite estas precauciones, es un error grave de seguridad (M2 = 1). Verificar mención a CISFraCAM como referencia argentina.

---

### Pregunta #003
**Área**: Traumatología
**Tema**: Hombro doloroso — Evaluación
**Dificultad**: Básico
**Modo**: Estudiante
**Pregunta**: ¿Qué tests clínicos se utilizan para evaluar el síndrome de pinzamiento subacromial y qué estructura está comprometida?
**Respuesta esperada**:
El síndrome de pinzamiento subacromial compromete el tendón del supraespinoso (más frecuente), la bursa subacromial y/o el tendón de la porción larga del bíceps contra el arco coracoacromial.

**Tests clínicos principales**:
1. **Test de Neer**: Flexión pasiva del hombro con escápula fijada. Positivo si reproduce dolor entre 60-120°. Evalúa pinzamiento de supraespinoso contra borde anterior del acromion.
2. **Test de Hawkins-Kennedy**: Hombro en flexión 90°, codo 90°, rotación interna forzada. Positivo si dolor. Mayor sensibilidad que Neer para pinzamiento.
3. **Test de Jobe (Empty Can Test)**: Hombro en abducción 90°, rotación interna (pulgar hacia abajo), 30° de flexión horizontal. Resistencia a la abducción. Positivo si dolor o debilidad → supraespinoso.
4. **Test de Yocum**: Mano sobre hombro contralateral, elevar el codo contra resistencia. Positivo si dolor subacromial.
5. **Test de Speed**: Flexión de hombro contra resistencia con codo extendido y antebrazo supinado. Positivo si dolor en corredera bicipital → porción larga del bíceps.

**Recordar**: El arco doloroso entre 60-120° de abducción activa es característico del pinzamiento (impingement).

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/guia-hombro-doloroso.md`
- `knowledge_base/libros/biomecanica-kapandji.md` (Tomo I — Miembro Superior)
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`

**Ejes OSCE a evaluar**:
- Primarios: D1 (precisión diagnóstica), D2 (diagnóstico diferencial — descartar tendinopatía del manguito vs. capsulitis), D4 (relación anatomofuncional)
- Secundarios: C3 (valor pedagógico), C1, K1

**Notas para el evaluador**: En modo estudiante, debe explicar cada test con detalle anatómico. Un error común es confundir el test de Jobe con el de Patte (que evalúa infraespinoso). Verificar que mencione la relación anatómica (supraespinoso → acromion → pinzamiento).

---

### ÁREA: NEUROLOGÍA

---

### Pregunta #004
**Área**: Neurología
**Tema**: Rehabilitación post ACV — Fases
**Dificultad**: Intermedio
**Modo**: Profesional
**Pregunta**: Según el Consenso de ACV Isquémico Agudo (Revista Medicina Buenos Aires, 2019), ¿cuáles son las fases de rehabilitación kinésica post ACV y qué objetivos se persiguen en cada una?
**Respuesta esperada**:
Según el Consenso argentino publicado en Revista Medicina (Buenos Aires, 2019, Vol. 79 Supl. II):

**Fase I — Aguda (primeras 24-72 horas en UCI/Unidad de Stroke)**:
- Objetivos: Prevención de complicaciones por encamamiento (TVP, neumonía, úlceras por presión), posicionamiento terapéutico, movilización pasiva precoz, evaluación del estado de conciencia y deglución.
- Kinesioterapia respiratoria si hay compromiso pulmonar.

**Fase II — Subaguda (días 3 a semanas 2-4 en sala de rehabilitación)**:
- Objetivos: Recuperación del control postural (sedestación, bipedestación), inicio de transferencias, reeducación de la marcha si hay posibilidad, prevención de hombro doloroso hemiparético.
- Técnicas: Facilitación neuromuscular propioceptiva (FNP), concepto Bobath, terapia por restricción del lado sano si es factible.
- Escalas a utilizar: NIHSS, índice de Barthel modificado, escala de Rankin.

**Fase III — Rehabilitación (semanas 4 a meses 3-6)**:
- Objetivos: Maximizar independencia funcional, marcha comunitaria, reintegración de miembro superior en AVD, manejo de espasticidad si aparece.
- Terapia ocupacional integrada.

**Fase IV — Mantenimiento y reinserción (>6 meses hasta 1-2 años)**:
- Objetivos: Mantener logros funcionales, prevenir complicaciones secundarias, adaptación del hogar, reinserción social y laboral.

**Importante**: El consenso argentino enfatiza la "ventana de oportunidad" de los primeros 3 meses y recomienda un mínimo de 3 horas diarias de terapia interdisciplinaria en fase subaguda.

**Fuentes de referencia**:
- `knowledge_base/protocolos/consenso-acv-isquemico.md`
- `knowledge_base/protocolos/protocolo-acv.md`
- `knowledge_base/protocolos/protocolo-rehabilitacion-acv.md`
- `knowledge_base/libros/neurorehabilitacion-umphred.md`
- `knowledge_base/libros/neurorehabilitacion-bobath.md`

**Ejes OSCE a evaluar**:
- Primarios: M1 (adherencia a protocolos), D3, D6 (clasificación con NIHSS/Rankin), D7 (escalas funcionales), K3
- Secundarios: M4, M7, C4, C6

**Notas para el evaluador**: Debe citar el consenso argentino de Revista Medicina 2019. Verificar que mencione NIHSS, Barthel, Rankin como escalas de referencia. Error crítico: omitir la evaluación de deglución/disfagia (compromete M2).

---

### Pregunta #005
**Área**: Neurología
**Tema**: Lesión medular — Clasificación ASIA
**Dificultad**: Avanzado
**Modo**: Profesional
**Pregunta**: Un paciente con lesión medular traumática nivel C6 presenta función motora en C5 bilateral con fuerza 4/5, C6 derecho 2/5 e izquierdo 1/5, sensibilidad preservada hasta S4-S5. ¿Cómo clasifica según la escala ASIA y qué objetivos kinésicos son realistas a 6 meses?
**Respuesta esperada**:
**Clasificación ASIA**: ASIA C (motora incompleta — menos del 50% de los músculos clave por debajo del nivel tienen grado ≥3/5, pero hay función motora voluntaria preservada). Nivel neurológico: C6. Zona de preservación parcial: hasta nivel torácico (por sensibilidad en S4-S5).

**Puntaje motor**: Depende de los 10 pares musculares clave. Con C5 bilateral 4/5 = 20 puntos base. Si solo se preserva algo en C6, el puntaje motor total será bajo pero con potencial de mejora por ser lesión incompleta.

**Objetivos realistas a 6 meses**:
1. **Independencia ventilatoria**: Lesión C6 permite respiración diafragmática autónoma (inervación frénica C3-C5 preservada).
2. **Movilidad en cama**: Independencia con ayudas técnicas (barandas, escalerilla de cuerda).
3. **Transferencias**: Asistencia moderada-mínima con tabla de transferencia.
4. **Silla de ruedas**: Independiente en terreno plano con silla eléctrica o manual ultraliviana con aros recubiertos.
5. **AVD**: Alimentación independiente con adaptaciones (muñequera universal). Higiene con asistencia parcial.
6. **Marcha**: No es objetivo realista como modo primario de desplazamiento. Posible marcha terapéutica con ortesis largas bilaterales (KAFO + bastones) con alto gasto energético.
7. **Prevención de complicaciones**: Disreflexia autonómica (lesiones >T6 — en este caso aplica por ser C6), úlceras por presión, espasticidad, dolor neuropático.

**Fuentes de referencia**:
- `knowledge_base/protocolos/protocolo-lesion-medular.md` (INAREPs 2018)
- `knowledge_base/libros/neurorehabilitacion-umphred.md`
- `knowledge_base/libros/daniels-worthingham.md`

**Ejes OSCE a evaluar**:
- Primarios: D1, D6 (clasificación ASIA), D8 (pronóstico funcional), H5, M3 (personalización)
- Secundarios: D2, D4, M2, M7, K3

**Notas para el evaluador**: Esta pregunta evalúa razonamiento clínico avanzado. Verificar que KineIA no cometa el error frecuente de prometer marcha funcional en lesión C6. Debe calcular puntaje motor ASIA y mencionar disreflexia autonómica como riesgo.

---

### Pregunta #006
**Área**: Neurología
**Tema**: Parkinson — Tratamiento kinésico
**Dificultad**: Básico
**Modo**: Estudiante
**Pregunta**: ¿Cuáles son los objetivos del tratamiento kinésico en un paciente con Enfermedad de Parkinson en estadio moderado (Hoehn y Yahr III) y qué estrategias se utilizan para el manejo de la marcha?
**Respuesta esperada**:
En la Enfermedad de Parkinson estadio Hoehn y Yahr III (enfermedad bilateral con alteración del equilibrio, independiente para AVD), los objetivos kinésicos son:

1. **Mejorar la amplitud de movimiento**: Prevención de contracturas y deformidades posturales (flexión de tronco, protracción cervical).
2. **Mantener/mejorar el equilibrio**: Trabajo de reacciones de equilibrio, base de sustentación.
3. **Estrategias para la marcha parkinsoniana**:
   - **Señales externas (cueing)**: Líneas en el piso para mejorar longitud del paso, metrónomo auditivo para cadencia.
   - **Estrategias atencionales**: "Marcha de soldado" (pasos grandes y deliberados), pensar en sortear obstáculos.
   - **Giros**: Técnica de giro en "U" (arco amplio) en lugar de giro sobre el eje para evitar freezing.
   - **Freezing de la marcha**: Técnica de balanceo lateral ("paso del pingüino"), contar mentalmente, visualizar un obstáculo a superar.
4. **Transferencias**: Entrenamiento de cama-silla, suelo-bipedestación (técnica de 4 puntos).
5. **Fortalecimiento de extensores**: Glúteo mayor, cuádriceps, paravertebrales (contrarrestar patrón flexor).
6. **Coordinación y destreza**: Ejercicios de motricidad fina.

**Técnicas específicas**: LSVT BIG (Lee Silverman Voice Treatment — versión motora), entrenamiento con doble tarea (dual task training).

**Fuentes de referencia**:
- `knowledge_base/libros/neurologia-stokes.md`
- `knowledge_base/libros/neurorehabilitacion-umphred.md`
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`

**Ejes OSCE a evaluar**:
- Primarios: M3, M4, M7 (educación al paciente sobre la enfermedad), C3 (valor pedagógico)
- Secundarios: D4, D7, C1, C4

**Notas para el evaluador**: Esperado que en modo estudiante ofrezca una explicación didáctica con ejemplos concretos. Debe mencionar freezing y estrategias de cueing. LSVT BIG debe mencionarse como referencia aunque KineIA no tenga un documento específico sobre el tema (evaluar C5 — si admite el límite de su conocimiento).

---

### ÁREA: RESPIRATORIO

---

### Pregunta #007
**Área**: Respiratorio
**Tema**: EPOC — Rehabilitación pulmonar (GOLD 2024)
**Dificultad**: Intermedio
**Modo**: Profesional
**Pregunta**: Según la guía GOLD 2024, ¿cuáles son los componentes de un programa de rehabilitación pulmonar para un paciente EPOC grupo E y qué parámetros ventilatorios deben monitorearse durante el entrenamiento?
**Respuesta esperada**:
La guía GOLD 2024 define grupo E como pacientes con ≥2 exacerbaciones moderadas o ≥1 con hospitalización en el último año (independientemente del nivel de síntomas).

**Componentes del programa de rehabilitación pulmonar**:

1. **Entrenamiento de miembros inferiores**:
   - Modalidad: Cicloergómetro o cinta de marcha.
   - Intensidad: 60-80% de la carga máxima (test incremental) o Borg 4-6 (disnea/piernas).
   - Frecuencia: 3-5 sesiones/semana, mínimo 8 semanas (20-36 sesiones totales).
   - Duración: 20-60 min/sesión (progresivo).

2. **Entrenamiento de miembros superiores**:
   - Ejercicios con bandas elásticas, pesas ligeras, ergómetro de brazos.
   - Importante: el entrenamiento de MMSS reduce la disnea en AVD que requieren brazos (peinarse, ducharse).

3. **Entrenamiento de músculos respiratorios**:
   - Indicado si Pimax <60 cmH2O o <70% del predicho.
   - Dispositivo de carga umbral (Threshold IMT).
   - Intensidad: ≥30% de la Pimax.
   - 30 minutos/día o 15 minutos 2 veces al día.

4. **Educación terapéutica**:
   - Técnica de ahorro de energía (respiración con labios fruncidos).
   - Reconocimiento de exacerbaciones (cambios en esputo, disnea).
   - Uso correcto de inhaladores.

5. **Soporte nutricional y psicosocial**.

**Parámetros ventilatorios a monitorear**:
- **SpO2**: Mantener ≥88-90% durante el ejercicio. Si desatura <88% → O2 suplementario.
- **Frecuencia respiratoria**: No exceder 30-35 rpm.
- **Borg disnea y fatiga**: Mantener 4-6 (moderado-intenso).
- **FC**: 60-80% FCmáx teórica o FC de reserva (Karvonen).

**Contraindicaciones para rehabilitación pulmonar**: Enfermedad cardiovascular inestable, deterioro cognitivo severo, incapacidad para deambular (excepto programas adaptados).

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/guia-epoc-gold-2024.md`
- `knowledge_base/guias-clinicas/consenso-rehabilitacion-respiratoria-argentina.md`
- `knowledge_base/libros/kinesiologia-respiratoria-postiaux.md`

**Ejes OSCE a evaluar**:
- Primarios: M1 (adherencia a GOLD 2024), M5 (dosificación precisa), M2 (contraindicaciones, SpO2)
- Secundarios: D6 (clasificación GOLD), D5 (parámetros ventilatorios), M6, K4

**Notas para el evaluador**: Verificar actualización a GOLD 2024 (no GOLD 2023 — el grupo ABCD cambió a ABE). Debe especificar intensidad con Borg. La ausencia de mención a SpO2 durante ejercicio es un error de seguridad (M2).

---

### Pregunta #008
**Área**: Respiratorio
**Tema**: Técnicas de fisioterapia respiratoria
**Dificultad**: Básico
**Modo**: Estudiante
**Pregunta**: ¿Qué técnicas de higiene bronquial existen en kinesiología respiratoria y cuándo está indicada cada una? Describí al menos 5 técnicas.
**Respuesta esperada**:
Las técnicas de higiene bronquial buscan la permeabilización de la vía aérea eliminando secreciones:

1. **Drenaje postural**: Posicionamiento con segmento pulmonar a drenar hacia arriba (gravedad). Complementado con percusión (clapping) o vibración manual. Útil en bronquiectasias, fibrosis quística. Contraindicado en reflujo gastroesofágico severo.

2. **Técnica de espiración forzada (FET/Huffing)**: Espiración con glotis abierta ("empañando un espejo"). Menor riesgo de colapso de vía aérea que la tos. Indicada en EPOC.

3. **Ciclo activo de la respiración (ACBT)**: Combina control respiratorio + ejercicios de expansión torácica + FET. Estándar actual para la mayoría de patologías obstructivas.

4. **Drenaje autógeno**: Técnica de respiración a diferentes volúmenes pulmonares para movilizar secreciones de distal a proximal sin colapso. Requiere entrenamiento del paciente.

5. **Presión espiratoria positiva (PEP)**: Dispositivo que genera resistencia espiratoria. Puede ser PEP oscilante (Flutter, Acapella) que combina vibración + presión.

6. **Tos asistida manualmente**: Compresión toracoabdominal sincronizada con el esfuerzo de tos. Indicada en enfermedades neuromusculares con debilidad de prensa abdominal (ELA, distrofias).

7. **Ventilación percusiva intrapulmonar (IPV)**: Dispositivo que administra ciclos de presión positiva con alta frecuencia. Indicada en patologías con secreciones muy espesas.

**Selección según patología**:
- **EPOC**: ACBT + FET (evitar clapping por riesgo de broncoespasmo).
- **Fibrosis quística**: Drenaje postural + PEP oscilante + ACBT.
- **Enfermedad neuromuscular**: Tos asistida + IPV (según necesidad).
- **Post-quirúrgico abdominal/torácico**: Inspiración profunda sostenida + FET + espirometría de incentivo.

**Fuentes de referencia**:
- `knowledge_base/libros/kinesiologia-respiratoria-postiaux.md`
- `knowledge_base/guias-clinicas/consenso-rehabilitacion-respiratoria-argentina.md`
- `knowledge_base/guias-clinicas/guia-kinesiologia-respiratoria-adulto.md`

**Ejes OSCE a evaluar**:
- Primarios: D2 (selección según patología), M6 (técnicas como agentes), C3 (valor pedagógico — explicar cada técnica)
- Secundarios: D3, C1, C4, K1

**Notas para el evaluador**: En modo estudiante, debe explicar "por qué" funciona cada técnica, no solo nombrarlas. Un error conceptual grave sería indicar clapping en EPOC con hiperreactividad bronquial (desencadena broncoespasmo). Verificar que diferencie entre técnicas de higiene bronquial vs. reexpansión pulmonar.

---

### Pregunta #009
**Área**: Respiratorio
**Tema**: Espirometría — Interpretación
**Dificultad**: Intermedio
**Modo**: Estudiante
**Pregunta**: Me dan un paciente con los siguientes valores espirométricos: FEV1 58% del predicho, FVC 78% del predicho, FEV1/FVC 0.62. A las 2 semanas repito la espirometría post-broncodilatador y obtengo: FEV1 63%, FVC 80%, FEV1/FVC 0.64. ¿Cómo interpretás este resultado?
**Respuesta esperada**:
**Interpretación**:
1. **Obstrucción presente**: El cociente FEV1/FVC es 0.62, menor al límite inferior normal (LIN) o <0.70. Esto indica un patrón obstructivo. Post-broncodilatador, el cociente sigue bajo (0.64) → obstrucción no completamente reversible.
2. **Severidad**: FEV1 58% del predicho → GOLD 2 (moderado) según clasificación de severidad espirométrica. Post-broncodilatador mejora levemente (63%) pero sigue en rango moderado.
3. **Respuesta al broncodilatador**: La mejora del FEV1 es de 63-58=5% (cambio porcentual: 5/58 = 8.6%). Significativa si es ≥12% Y ≥200 mL. Aquí no alcanza el umbral → **no hay respuesta broncodilatadora significativa**. Esto sugiere EPOC más que asma.
4. **Diagnóstico presuntivo**: EPOC con obstrucción moderada (GOLD 2). Se requiere más información clínica (tabaquismo, síntomas, CAT, mMRC) para completar la clasificación ABE.

**Resumen**: Patrón obstructivo moderado, no completamente reversible post-broncodilatador → compatible con **EPOC GOLD 2**.

**Recordar**: La relación FEV1/FVC debe ser post-broncodilatador. Si la pre-broncodilatador es baja y post-broncodilatador se normaliza (>0.70 en adultos) → podría ser asma. En EPOC, la obstrucción es persistente.

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/guia-epoc-gold-2024.md`
- `knowledge_base/guias-clinicas/consenso-rehabilitacion-respiratoria-argentina.md`
- `knowledge_base/libros/kinesiologia-respiratoria-postiaux.md`

**Ejes OSCE a evaluar**:
- Primarios: D1 (diagnóstico), D5 (interpretación de estudios), D6 (clasificación de severidad)
- Secundarios: D2 (diferenciar asma vs. EPOC), D3, C3, K4

**Notas para el evaluador**: Debe calcular si la respuesta al broncodilatador es significativa (≥12% y ≥200 mL). Error común: diagnosticar solo con pre-broncodilatador o no calcular el delta porcentual. En modo estudiante, debe explicar el razonamiento paso a paso.

---

### ÁREA: DEPORTE

---

### Pregunta #010
**Área**: Deporte
**Tema**: Lesiones musculares — Clasificación y RTP
**Dificultad**: Intermedio
**Modo**: Profesional
**Pregunta**: ¿Cómo se clasifica una lesión muscular de isquiotibiales según la clasificación de Múnich y cuáles son los criterios de retorno al deporte (return to play)?
**Respuesta esperada**:
**Clasificación de Múnich (Consenso 2012, actualizada)**:

Tipo 1 — **Trastorno funcional** (sin evidencia de daño estructural en imágenes):
- 1A: Fatiga — dolor difuso post-ejercicio.
- 1B: DOMS (Delayed Onset Muscle Soreness) — dolor muscular de inicio tardío, inflamatorio.

Tipo 2 — **Lesión estructural** (evidencia de daño en imágenes):
- 2A: Lesión de fibras menores (elongación, distensión). Edema sin discontinuidad.
- 2B: Lesión de fibras parcial moderada. Discontinuidad parcial del fascículo.
- 2C: Lesión de fibras parcial extensa o completa (avulsión tendinosa).

Tipo 3 — **Contusión**:
- 3A: Leve-moderada (hematoma intramuscular sin pérdida funcional).
- 3B: Severa (hematoma extenso con síndrome compartimental potencial).

Tipo 4 — **Lesión sin distracción ni contusión**: Asociadas a enfermedad sistémica o patología neuromuscular subyacente.

**Criterios de Return to Play (RTP)**:
1. **Clínicos**:
   - Sin dolor a la palpación del vientre muscular.
   - ROM completo y simétrico (comparación bilateral).
   - Fuerza isométrica ≥90% del lado sano (dinamometría manual o isocinética).
   - Sin dolor durante el estiramiento funcional.

2. **Funcionales**:
   - Test de fuerza excéntrica (Nordic hamstring) asintomático.
   - Sprint progresivo sin dolor (50% → 100% velocidad).
   - Test de agilidad y cambio de dirección sin limitación.
   - Retorno gradual a entrenamiento específico (1-2 semanas mínimo).

3. **Tiempos estimados según clasificación**:
   - Grado 1-2A: 1-3 semanas.
   - Grado 2B: 4-8 semanas.
   - Grado 2C (avulsión): 3-6 meses (quirúrgico + rehab).

**Fuentes de referencia**:
- `knowledge_base/libros/kinesiologia-deportiva-prentice.md`
- `knowledge_base/libros/biomecanica-hamill.md`
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`

**Ejes OSCE a evaluar**:
- Primarios: D1 (clasificación), D6, M8 (criterios de RTP), D8 (pronóstico con tiempos)
- Secundarios: M3 (personalización según deporte), M4, K2, K4

**Notas para el evaluador**: La clasificación de Múnich es el estándar actual. Error: usar clasificación antigua (grado 1-2-3 simple sin subtipos). Verificar que los criterios de RTP incluyan test excéntrico (Nordic hamstring) — es el gold standard para isquiotibiales.

---

### Pregunta #011
**Área**: Deporte
**Tema**: Tendinopatía aquiliana
**Dificultad**: Avanzado
**Modo**: Profesional
**Pregunta**: Un corredor de 35 años presenta dolor en tendón de Aquiles de 3 meses de evolución, VISA-A score de 55/100. En ecografía se observa engrosamiento fusiforme con neovascularización pero sin rotura. ¿Cuál es el enfoque kinésico basado en evidencia actual para esta tendinopatía aquiliana insertional?
**Respuesta esperada**:
**Diagnóstico**: Tendinopatía aquiliana no insertional (2-6 cm proximal a inserción), crónica (3 meses), moderada-severa (VISA-A 55/100 — anormal; normal ≥95).

**Tratamiento kinésico basado en evidencia (escalonado de 12 semanas)**:

**Fase 1 — Control del dolor (Semanas 1-2)**:
- **Modificación de carga**: Reducción del volumen de carrera al nivel que no provoque dolor >3/10 (NRS). Reemplazo con cross-training (natación, ciclismo).
- **Ejercicio isométrico**: Contracción isométrica de tríceps sural 5 series × 45 segundos, 70% de CVM, 3-4 veces/día. Efecto analgésico inmediato (reduce inhibición cortical).
- Crioterapia post-ejercicio (analgesia).

**Fase 2 — Carga progresiva (Semanas 3-8)**:
- **Carga pesada y lenta (Heavy Slow Resistance — HSR)**: Elevación de talón 3-4 series × 6-15 RM, 3 segundos concéntrica + 3 segundos excéntrica. 3 veces/semana. Progresar en carga (kg) semanalmente.
- **Ejercicio excéntrico**: Protocolo de Alfredson modificado (evitar ir a dorsiflexión máxima en fase inicial si es muy doloroso).
- **Isométricos** como pre-activación y analgesia pre-ejercicio.

**Fase 3 — Retorno a la carrera (Semanas 9-12+)**:
- **Progresión gradual**: Inicio con trote en cinta (menor impacto), 5 minutos → progresar 5-10% por semana.
- **Almacenamiento y liberación de energía elástica**: Ejercicios pliométricos progresivos (saltos a dos piernas → una pierna → skipping).
- Continuar HSR 2 veces/semana como mantenimiento.

**Contraindicado para este caso**:
- NO usar AINEs crónicos (interfieren con la regeneración tendinosa).
- NO inyecciones de corticoides (riesgo de rotura).
- NO estiramientos estáticos agresivos en fase dolorosa.
- Cuidado con ejercicios en dorsiflexión máxima si es insertional (compresión del tendón contra el calcáneo).

**Evidencia**: Los programas de carga pesada y lenta (HSR) muestran resultados superiores en satisfacción del paciente vs. excéntrico puro (Beyer et al., 2015). La combinación isométrico + HSR tiene respaldo nivel I de evidencia.

**Fuentes de referencia**:
- `knowledge_base/libros/kinesiologia-deportiva-prentice.md`
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`
- `knowledge_base/libros/biomecanica-hamill.md`

**Ejes OSCE a evaluar**:
- Primarios: D1, M5 (dosificación — series, RM, frecuencia), M3 (personalización para corredor), M2 (contraindicaciones)
- Secundarios: D3, D5 (ecografía), D8, M4, K2

**Notas para el evaluador**: Evaluación rigurosa de dosificación (isométricos 5×45seg, HSR 3-4×6-15RM). Debe diferenciar tendinopatía insertional vs. no insertional (impacta en la prescripción de ejercicios). Error: prescribir protocolo de Alfredson estándar a un caso insertional sin modificaciones.

---

### Pregunta #012
**Área**: Deporte
**Tema**: Prevención de lesiones — FIFA 11+
**Dificultad**: Básico
**Modo**: Estudiante
**Pregunta**: ¿Qué es el programa FIFA 11+ y cuál es su efectividad demostrada en la prevención de lesiones en futbolistas?
**Respuesta esperada**:
El **FIFA 11+** es un programa de calentamiento neuromuscular desarrollado por el FIFA Medical Assessment and Research Centre (F-MARC) para la prevención de lesiones en fútbol.

**Estructura** (3 partes, 20 minutos total):
1. **Parte 1 — Ejercicios de carrera (8 min)**: Carrera lineal, carrera con cadera hacia afuera/adentro, carrera alrededor del compañero, saltos de contacto, carrera con cambios de dirección. Velocidad progresiva.
2. **Parte 2 — Fuerza, pliometría y equilibrio (10 min)**: 6 ejercicios con 3 niveles de dificultad cada uno:
   - Plancha (isométrica y dinámica) — core.
   - Isquiotibiales (Nordic hamstring) — fundamental.
   - Equilibrio unipodal (estático y dinámico con pases).
   - Sentadillas (bipodal → unipodal con banda).
   - Saltos verticales y laterales.
3. **Parte 3 — Carrera de alta intensidad (2 min)**: Sprints, skipping, carrera de aceleración/desaceleración, corte y cambio de dirección a máxima velocidad.

**Efectividad demostrada**:
- **Reducción de lesiones totales**: 30-50% (ensayos controlados aleatorizados).
- **Reducción de lesiones graves** (>28 días de baja): hasta 45%.
- **Reducción específica de lesiones de LCA**: 50% en mujeres futbolistas.
- **Mejora del rendimiento neuromuscular**: Aumento de fuerza de isquiotibiales (ratio H/Q), mejora de equilibrio, altura de salto vertical.
- **Relación costo-beneficio excelente**: Previene 1 lesión por cada 60-80 sesiones realizadas.

**Fuentes de referencia**:
- `knowledge_base/libros/kinesiologia-deportiva-prentice.md`
- `knowledge_base/libros/biomecanica-hamill.md`
- `knowledge_base/libros/ejercicio-terapeutico-kisner-colby.md`

**Ejes OSCE a evaluar**:
- Primarios: M7 (educación — prevención), C3 (valor pedagógico), M1
- Secundarios: D3, C1, C4, K4

**Notas para el evaluador**: En modo estudiante, debe poder describir el programa de forma didáctica. El Nordic hamstring es el componente más importante para prevenir lesión de isquiotibiales. Debe mencionar las tasas de reducción con respaldo de ECA.

---

### ÁREA: UCI

---

### Pregunta #013
**Área**: UCI (Terapia Intensiva)
**Tema**: Destete de ventilación mecánica
**Dificultad**: Avanzado
**Modo**: Profesional
**Pregunta**: ¿Cuáles son los criterios para iniciar una prueba de respiración espontánea (SBT) en un paciente que está en ventilación mecánica con modalidad VCV y qué parámetros se deben monitorear durante la prueba?
**Respuesta esperada**:
Según los estándares SATI y la evidencia actual en cuidados críticos:

**Criterios PRE-SBT (todos deben cumplirse)**:
1. **Causa de la falla respiratoria resuelta o en mejoría**: Resolución del shock, sepsis controlada, sobrecarga hídrica corregida.
2. **Estado hemodinámico estable**: Sin drogas vasoactivas a dosis altas, PAM ≥65 mmHg sin soporte significativo.
3. **Oxigenación adecuada**: PaO2 ≥60 mmHg con FiO2 ≤0.40, PEEP ≤8 cmH2O. PaO2/FiO2 >150-200.
4. **Mecánica ventilatoria**: Frecuencia respiratoria espontánea ≤35 rpm, Vt espontáneo >5 mL/kg, f/Vt (Rapid Shallow Breathing Index — RSBI) <105 resp/min/L.
5. **Estado neurológico**: Glasgow ≥8-10 (según contexto), capacidad de toser y manejar secreciones, reflejo tusígeno presente.
6. **Estado ácido-base**: pH ≥7.30-7.35.
7. **Electrolitos normales**: K+, Mg+, fosfato — la hipofosfatemia severa es causa de falla de destete.

**Modalidades de SBT**:
- **Tubo en T (T-piece)**: Paciente desconectado del ventilador, O2 suplementario humidificado. Es la más demandante y la más predictiva de éxito.
- **CPAP**: Presión continua en vía aérea (5 cmH2O) sin ciclado. Compensa la resistencia del tubo.
- **PSV baja**: Presión de soporte 5-7 cmH2O + PEEP 5 cmH2O. Simula condiciones post-extubación. Preferida actualmente en muchas UCI.

**Parámetros a monitorear DURANTE la SBT (criterios de falla)**:
1. **FR >35 rpm por >5 minutos**.
2. **SpO2 <90%**.
3. **FC >140 lpm o aumento >20% del basal**.
4. **PAS >180 mmHg o <90 mmHg**.
5. **Signos de distress**: uso de músculos accesorios, tiraje, aleteo nasal, respiración paradójica, diaforesis, agitación o disminución del sensorio.
6. **Arritmia nueva**.
7. **Acidosis respiratoria**: PaCO2 aumenta >10 mmHg y pH <7.30.

**Duración de la SBT**: 30-120 minutos. Si el paciente tolera ≥30 minutos sin signos de falla → considerar extubación.

**Evaluación kinésica post-SBT para extubación**:
- Capacidad tusígena efectiva (pico flujo de tos >60 L/min).
- Cantidad y calidad de secreciones (mínimas, fluidas).
- Fuerza de prensión manual como marcador de fuerza muscular global.
- Ausencia de estridor (test de fuga — cuff leak test).

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/kinesiologia-uci-argentina.md`
- `knowledge_base/guias-clinicas/guia-movilizacion-temprana-uci.md`
- `knowledge_base/protocolos/protocolo-vm-destete.md`
- `knowledge_base/libros/terapia-intensiva-cristancho.md`

**Ejes OSCE a evaluar**:
- Primarios: D5 (parámetros ventilatorios), M2 (seguridad — criterios de falla), D6
- Secundarios: H4 (red flags — signos de distress), M1 (protocolo SATI), D3, K3

**Notas para el evaluador**: Pregunta de alta complejidad. FUNDAMENTAL: RSBI <105 (error común: confundir punto de corte). Debe mencionar los 3 modos de SBT. Si omite los criterios de falla durante la SBT, es un error grave de seguridad. La evaluación kinésica post-SBT (tos, secreciones, cuff leak test) debe estar presente.

---

### Pregunta #014
**Área**: UCI (Terapia Intensiva)
**Tema**: Movilización temprana
**Dificultad**: Intermedio
**Modo**: Profesional
**Pregunta**: ¿Cuáles son los criterios de inclusión, exclusión y los niveles de movilización temprana en un paciente crítico según el protocolo de movilización temprana en UCI?
**Respuesta esperada**:
**Definición**: Movilización temprana es la aplicación de actividad física dentro de las primeras 24-72 horas de ingreso a UCI, progresando desde movilización pasiva hasta deambulación asistida.

**Criterios de INCLUSIÓN (todos deben cumplirse)**:
- **Neurológico**: RASS (Richmond Agitation Sedation Scale) ≥-2 (responde a estímulo verbal). Capaz de seguir órdenes simples.
- **Respiratorio**: FiO2 ≤0.60, PEEP ≤10 cmH2O, sin distress respiratorio.
- **Hemodinámico**: PAM ≥60 mmHg (sin aumento de drogas en las últimas 2 horas). FC 50-120 lpm. Sin arritmia aguda.
- **Sin contraindicación absoluta**.

**Criterios de EXCLUSIÓN (cualquiera presente = NO movilizar)**:
- **Absolutas**: Hipertensión endocraneana (PIC >20 mmHg), fractura inestable de columna o pelvis, sangrado activo no controlado, isquemia aguda de miembro inferior, IAM reciente (<24h), arritmia maligna no controlada, cirugía abdominal abierta con riesgo de evisceración.
- **Relativas (precaución)**: Droga vasoactiva en aumento, balón de contrapulsación intraaórtico (por vía femoral), fiebre >39°C, trombosis venosa profunda aguda sin filtro.

**Niveles de movilización progresiva**:
1. **Nivel 1 — Pasiva en cama**: ROM pasivo de 4 miembros, cambios posturales cada 2 horas. Indicado si RASS ≤-3.
2. **Nivel 2 — Activa/asistida en cama**: ROM activo, ejercicios contra resistencia manual, sentarse asistido al borde de la cama (dangling). Indicado si RASS ≥-2.
3. **Nivel 3 — Bipedestación**: Pasar de sedestación a bipedestación asistida (con o sin ayuda de bipedestador/tabla). Evaluar hipotensión ortostática.
4. **Nivel 4 — Transferencia a silla**: Sedestación en sillón reclinable o silla de ruedas. Primera vez: 15-30 minutos, progresar según tolerancia.
5. **Nivel 5 — Deambulación estática**: Marcha en el lugar, desplazamiento de peso en bipedestación.
6. **Nivel 6 — Deambulación asistida**: Marcha con andador o bastones con asistencia según necesidad. Meta: independencia funcional.

**Criterios de DETENCIÓN de la sesión**:
- FR >35 rpm o <5 rpm.
- SpO2 <88% >3 minutos.
- FC >130 lpm o <40 lpm.
- Hipotensión (PAM <55 mmHg).
- Dolor torácico.
- Agotamiento o solicitud del paciente.
- Caída >10 puntos en la PAM durante la bipedestación (hipotensión ortostática).

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/guia-movilizacion-temprana-uci.md`
- `knowledge_base/guias-clinicas/kinesiologia-uci-argentina.md`
- `knowledge_base/libros/terapia-intensiva-cristancho.md`

**Ejes OSCE a evaluar**:
- Primarios: M2 (seguridad — contraindicaciones), M4 (progresión por niveles), H4
- Secundarios: H6 (escala RASS), M7, C4, K3

**Notas para el evaluador**: El kinesiólogo de UCI debe conocer los niveles de movilización y los criterios de detención. Error grave: no mencionar RASS o no tener en cuenta PIC en TEC. Verificar que la progresión esté correctamente secuenciada (no saltar de cama a deambular sin pasar por sedestación y bipedestación).

---

### Pregunta #015
**Área**: UCI (Terapia Intensiva)
**Tema**: Posición prono en SDRA
**Dificultad**: Avanzado
**Modo**: Profesional
**Pregunta**: ¿Cuál es la indicación, contraindicaciones y rol del kinesiólogo durante la maniobra de decúbito prono en un paciente con SDRA moderado-severo en ventilación mecánica?
**Respuesta esperada**:
**Indicación según SATI/evidencia internacional**:
- SDRA moderado-severo: PaO2/FiO2 <150 con FiO2 ≥0.60 y PEEP ≥10 cmH2O.
- Realizar dentro de las primeras 36 horas de cumplir criterios.
- Duración: mínimo 16 horas continuas por sesión (ideal 16-20 horas).

**Contraindicaciones ABSOLUTAS**:
- Inestabilidad hemodinámica refractaria.
- Hipertensión endocraneana no controlada (PIC >30 mmHg).
- Fractura inestable de columna (sin fijación).
- Cirugía abdominal reciente con abdomen abierto.
- Hemoptisis masiva activa.
- Embarazo >20 semanas (por compresión de vena cava).

**Contraindicaciones RELATIVAS**:
- Traqueostomía reciente (<24 horas).
- Drenajes torácicos anteriores (riesgo de acodamiento).
- Quemaduras extensas en cara o tórax anterior.
- Lesiones faciales.

**Rol del kinesiólogo**:
1. **Pre-maniobra**:
   - Aspiración de secreciones bronquiales y de vía aérea artificial.
   - Verificar fijación del TOT/TQT (reforzar si es necesario).
   - Proteger ojos con parche y proteger prominencias óseas (cara, mamas, crestas ilíacas, rodillas, genitales, dedos de pies).
   - Asegurar drenajes, sondas, accesos vasculares (fijar y dejar holgura suficiente).
   - Evaluar previamente si el circuito del VM permite la rotación sin desconexión.

2. **Durante la maniobra (coordinación con enfermería)**:
   - Se requieren mínimo 4-5 operadores (el kinesiólogo lidera el comando de giro).
   - Técnica de giro: Maniobra en bloque ("sandwich" con sábanas). Giro de decúbito supino a lateral y luego a prono.
   - Operador 1 (kinesiólogo): Protege vía aérea y cabeza. Coordina los tiempos del giro.
   - Verificar inmediatamente: posición del TOT/TQT, conexión al VM, curvas del ventilador (volumen corriente, presiones), SpO2.

3. **Post-maniobra**:
   - Posicionamiento terapéutico (natación/prono): Un brazo hacia arriba, otro hacia abajo, cambiar cada 2-4 horas.
   - Proteger puntos de apoyo con almohadillas.
   - Monitorizar respuesta gasométrica: PaO2/FiO2 debe mejorar en 2-4 horas. Si no mejora → considerar retirar el prono (no respondedor).

**Fisiología del decúbito prono (por qué funciona)**:
- Reclutamiento de zonas dorsales atelectásicas (relación V/Q más homogénea).
- Disminución de la compresión cardíaca sobre el pulmón izquierdo.
- Mejor drenaje de secreciones bronquiales.
- Disminución del gradiente de presión pleural (dorsal-ventral más homogéneo).

**Fuentes de referencia**:
- `knowledge_base/guias-clinicas/kinesiologia-uci-argentina.md`
- `knowledge_base/guias-clinicas/guia-movilizacion-temprana-uci.md`
- `knowledge_base/protocolos/protocolo-vm-destete.md`
- `knowledge_base/libros/terapia-intensiva-cristancho.md`

**Ejes OSCE a evaluar**:
- Primarios: M2 (seguridad — contraindicaciones y protección), D5 (PaO2/FiO2), D4
- Secundarios: M1, D3, K3 (contexto SATI), C4

**Notas para el evaluador**: Pregunta que evalúa conocimiento muy específico de UCI. KineIA debe describir el rol del kinesiólogo más allá de solo nombrarlo. Debe diferenciar contraindicaciones absolutas de relativas. Si omite la protección de prominencias óseas o la verificación del TOT post-giro, es un error de seguridad (M2 = 1-2).

---

## Hoja de ruta del banco por área (175 espacios pendientes)

A continuación se planifican 190 espacios distribuidos por área: 15 ya están completos y 175 siguen pendientes. Esta planificación debe ampliarse en al menos 10 entradas para alcanzar el objetivo de 200+ pares completos.

---

### TRAUMATOLOGÍA (30 preguntas — completar 27 restantes)

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 004 | Clasificación de fracturas (AO/OTA) | Básico | Estudiante |
| 005 | Artrosis de rodilla — Tratamiento conservador | Intermedio | Profesional |
| 006 | Prótesis total de rodilla — Rehabilitación post-Qx | Intermedio | Profesional |
| 007 | Síndrome de pinzamiento subacromial — Tests (Neer, Hawkins, Jobe) | Básico | Estudiante |
| 008 | Capsulitis adhesiva de hombro — Fases y manejo kinésico | Intermedio | Profesional |
| 009 | Epicondilitis lateral — Fisiopatología y tratamiento | Intermedio | Estudiante |
| 010 | Esguince de tobillo — Clasificación y rehabilitación funcional | Básico | Estudiante |
| 011 | Fractura de Colles — Protocolo de rehabilitación | Intermedio | Profesional |
| 012 | Luxación glenohumeral anterior — Rehabilitación post-reducción | Intermedio | Profesional |
| 013 | Pubalgia — Diagnóstico diferencial y protocolo de rehabilitación | Avanzado | Profesional |
| 014 | Amputación de miembro inferior — Niveles y abordaje kinésico | Avanzado | Profesional |
| 015 | Consolidación ósea — Fases y factores que la afectan | Básico | Estudiante |
| 016 | Síndrome femoropatelar — Evaluación y tratamiento | Intermedio | Profesional |
| 017 | Lesión de meniscos — Protocolo conservador vs. quirúrgico | Intermedio | Profesional |
| 018 | Escoliosis idiopática del adolescente — Rol kinésico | Intermedio | Profesional |
| 019 | Artritis reumatoidea — Manejo kinésico en mano | Avanzado | Profesional |
| 020 | Electromiografía — Fundamentos para kinesiólogos | Avanzado | Estudiante |
| 021 | Concepto Mulligan — MWM en rodilla y tobillo | Intermedio | Profesional |
| 022 | Vendaje neuromuscular (Kinesiotape) — Aplicaciones en hombro | Básico | Estudiante |
| 023 | Onda de choque extracorpórea — Indicaciones y parámetros | Avanzado | Profesional |
| 024 | Magnetoterapia — Indicaciones en fracturas | Básico | Estudiante |
| 025 | Láser terapéutico — Parámetros y aplicaciones | Intermedio | Profesional |
| 026 | Punción seca — Rol del kinesiólogo en Argentina | Avanzado | Profesional |
| 027 | Isocinéticos — Evaluación de fuerza muscular | Avanzado | Profesional |
| 028 | Cadena cinética cerrada vs. abierta — Aplicación clínica | Básico | Estudiante |
| 029 | Entrenamiento propioceptivo — Tobillo post-esguince | Intermedio | Estudiante |
| 030 | Fractura de estrés — Factores de riesgo y manejo en deportistas | Avanzado | Profesional |

---

### NEUROLOGÍA (30 preguntas — completar 27 restantes)

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 007 | Clasificación ASIA — Lesión medular (caso clínico C6) | Avanzado | Profesional |
| 008 | Esclerosis Múltiple — Evaluación y tratamiento kinésico | Intermedio | Profesional |
| 009 | Reflejo miotático — Evaluación y alteraciones | Básico | Estudiante |
| 010 | Tono muscular — Escala de Ashworth modificada | Básico | Estudiante |
| 011 | Marcha hemiparética — Características y fases | Intermedio | Estudiante |
| 012 | Concepto Bobath — Principios y aplicación en ACV | Intermedio | Profesional |
| 013 | Afasia — Tipos y comunicación con el paciente | Básico | Estudiante |
| 014 | Hombro doloroso hemiparético — Prevención y manejo | Intermedio | Profesional |
| 015 | Negligencia espacial — Evaluación y tratamiento | Avanzado | Profesional |
| 016 | Terapia por restricción del lado sano (CIMT) — Evidencia | Avanzado | Profesional |
| 017 | Escala de Rankin modificada — Interpretación | Básico | Estudiante |
| 018 | Neuroplasticidad — Principios y aplicación clínica | Intermedio | Estudiante |
| 019 | Lesión de nervio periférico — Clasificación de Seddon | Intermedio | Estudiante |
| 020 | Parálisis facial periférica — Evaluación y manejo | Intermedio | Profesional |
| 021 | Síndrome de Guillain-Barré — Fases y manejo kinésico | Avanzado | Profesional |
| 022 | Ataxia — Tipos y estrategias de rehabilitación | Intermedio | Profesional |
| 023 | Estimulación eléctrica funcional (FES) — Aplicación en ACV | Avanzado | Profesional |
| 024 | Transferencias en lesión medular C5-C6 | Intermedio | Profesional |
| 025 | Disreflexia autonómica — Fisiopatología y manejo agudo | Avanzado | Profesional |
| 026 | Escala de equilibrio de Berg — Aplicación e interpretación | Básico | Estudiante |
| 027 | Traumatismo encefalocraneano (TEC) — Evaluación kinésica | Avanzado | Profesional |
| 028 | Siringomielia — Consideraciones kinésicas | Avanzado | Profesional |
| 029 | Marcha atáxica vs. parkinsoniana vs. espástica | Intermedio | Estudiante |
| 030 | Electromiografía — Valores normales para kinesiólogo | Avanzado | Estudiante |

---

### RESPIRATORIO (30 preguntas — completar 27 restantes)

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 010 | Asma bronquial — Manejo kinésico durante crisis | Intermedio | Profesional |
| 011 | Auscultación pulmonar — Ruidos normales y patológicos | Básico | Estudiante |
| 012 | Atelectasia post-quirúrgica — Estrategias kinésicas | Intermedio | Profesional |
| 013 | Fibrosis quística — Rol del kinesiólogo | Intermedio | Profesional |
| 014 | Tos — Mecanismo y fases. Tos crónica vs productiva | Básico | Estudiante |
| 015 | Ventilación no invasiva (VNI) — Modos y aplicación | Avanzado | Profesional |
| 016 | Insuficiencia respiratoria tipo 1 vs tipo 2 | Básico | Estudiante |
| 017 | Espirometría de incentivo — Tipos y técnica correcta | Básico | Estudiante |
| 018 | Bronquiectasias — Higiene bronquial y autocuidado | Intermedio | Profesional |
| 019 | Oxigenoterapia — Dispositivos y flujos | Básico | Estudiante |
| 020 | Derrame pleural — Rol kinésico post-drenaje | Intermedio | Profesional |
| 021 | Neumonía adquirida en la comunidad — Manejo kinésico | Intermedio | Profesional |
| 022 | Técnica ELTGOL vs. drenaje autógeno vs. ACBT | Avanzado | Profesional |
| 023 | Prueba de marcha de 6 minutos — Protocolo y valores | Intermedio | Estudiante |
| 024 | Distensibilidad pulmonar — Concepto y aplicación en VM | Avanzado | Estudiante |
| 025 | Aspiración de secreciones — Técnica y precauciones | Intermedio | Profesional |
| 026 | Enfermedad neuromuscular respiratoria — ELA y distrofias | Avanzado | Profesional |
| 027 | CPAP vs. BiPAP — Indicaciones y diferencias | Intermedio | Estudiante |
| 028 | Gasometría arterial — Interpretación por kinesiólogo | Intermedio | Profesional |
| 029 | Entrenamiento de músculos inspiratorios — Threshold IMT | Intermedio | Profesional |
| 030 | Fisioterapia respiratoria en pediatría — Bronquiolitis | Intermedio | Profesional |

---

### DEPORTE (25 preguntas — completar 22 restantes)

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 013 | Test isocinético de rodilla — Interpretación | Avanzado | Profesional |
| 014 | Lesión muscular de cuádriceps — Grados y RTP | Intermedio | Profesional |
| 015 | Síndrome de sobreentrenamiento — Signos y abordaje | Intermedio | Profesional |
| 016 | Pubalgia en futbolista — Diagnóstico diferencial | Avanzado | Profesional |
| 017 | Propiocepción y control neuromuscular — Bases teóricas | Básico | Estudiante |
| 018 | Lesión de LCA en fútbol femenino — Factores de riesgo | Intermedio | Profesional |
| 019 | Crioterapia post-ejercicio — Evidencia y protocolos | Básico | Estudiante |
| 020 | Calentamiento pre-competitivo — Componentes según evidencia | Básico | Estudiante |
| 021 | Vendaje funcional de tobillo — Técnica y evidencia | Intermedio | Profesional |
| 022 | Recuperación post-partido — Estrategias kinésicas | Intermedio | Profesional |
| 023 | Entrenamiento pliométrico — Progresión y fases | Intermedio | Estudiante |
| 024 | Lesión de SLAP (labrum superior) en deportes de lanzamiento | Avanzado | Profesional |
| 025 | Readaptación deportiva — Diferencias con rehabilitación | Intermedio | Profesional |

---

### UCI (25 preguntas — completar 22 restantes)

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 016 | Modos ventilatorios — VCV, VPC, PSV, SIMV | Avanzado | Profesional |
| 017 | Parámetros ventilatorios — Vt, PEEP, FiO2, trigger | Intermedio | Estudiante |
| 018 | Aspiración en circuito cerrado vs abierto | Intermedio | Profesional |
| 019 | Cuff leak test — Procedimiento e interpretación | Avanzado | Profesional |
| 020 | Traqueostomía — Manejo kinésico y decanulación | Avanzado | Profesional |
| 021 | Síndrome de dificultad respiratoria aguda (SDRA) — Definición de Berlín | Avanzado | Profesional |
| 022 | Ventilación en prono — Rol kinésico y evidencia | Avanzado | Profesional |
| 023 | Polineuromiopatía del paciente crítico — Prevención y manejo | Avanzado | Profesional |
| 024 | Delirium en UCI — Rol del kinesiólogo | Intermedio | Profesional |
| 025 | Escala RASS y CAM-ICU — Interpretación | Básico | Estudiante |

---

### PEDIATRÍA (25 preguntas — completar 25 restantes)

Las preguntas pediátricas deben cubrir desarrollo motor normal (hitos, reflejos), parálisis cerebral (GMFCS), DCD (trastorno del desarrollo de la coordinación), tortícolis congénita, displasia de cadera, rehabilitación respiratoria pediátrica (bronquiolitis, fibrosis quística), escoliosis del adolescente, y tratamiento kinésico en condiciones genéticas (Down, Duchenne).

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 001 | Hitos del desarrollo motor 0-24 meses | Básico | Estudiante |
| 002 | Reflejos primitivos — Cronología de desaparición | Básico | Estudiante |
| 003 | Parálisis cerebral — Clasificación GMFCS | Intermedio | Profesional |
| 004 | Tortícolis congénita — Evaluación y manejo kinésico | Intermedio | Profesional |
| 005 | Bronquiolitis en lactantes — Criterios de derivación y manejo | Intermedio | Profesional |

---

### COLUMNA (25 preguntas — completar 25 restantes)

Las preguntas de columna deben cubrir dolor lumbar inespecífico (red flags, guías de práctica clínica), hernia discal lumbar y cervical, espondilolistesis, canal estrecho lumbar, escoliosis, rehabilitación post-quirúrgica (microdiscectomía, artrodesis), concepto McKenzie (MDT), estabilización segmentaria (core stability), y dolor cervical mecánico.

| # | Tema | Dificultad | Modo |
|---|------|------------|------|
| 001 | Dolor lumbar inespecífico — Red flags y manejo | Intermedio | Profesional |
| 002 | Hernia discal L4-L5 — Presentación clínica y tratamiento conservador | Intermedio | Profesional |
| 003 | Concepto McKenzie — Evaluación y clasificación (derangement, disfunción, postural) | Avanzado | Profesional |
| 004 | Síndrome de cola de caballo — Signos y derivación urgente | Avanzado | Profesional |
| 005 | Estabilización segmentaria lumbar — Core stability | Intermedio | Profesional |

---

## Información Técnica para el Script de Evaluación

Cada pregunta del benchmark debe tener su **respuesta esperada** en formato que el script `scripts/evaluate.py` pueda comparar con la respuesta de KineIA. Ver documentación en ese script para el formato exacto del CSV de entrada/salida.

**Formato CSV del benchmark** (exportable desde este markdown para uso automático):

```csv
id,area,tema,dificultad,modo,pregunta,respuesta_esperada,ejes_primarios,ejes_secundarios,fuentes
001,Traumatologia,Rehabilitacion LCA,Intermedio,Profesional,"¿Cuáles son las fases de rehabilitación post operatoria de LCA...","La rehabilitación post-reconstrucción...","M1,M4,M8,D3","H1,D4,C3,C4,K1,K2","protocolo-lca-rehabilitacion.md,protocolo-lca.md"
...
```
