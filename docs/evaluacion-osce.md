# Marco de Evaluación OSCE para KineIA

> **OSCE**: Objective Structured Clinical Examination — examen clínico objetivo y estructurado.
> Adaptación del marco utilizado por Google DeepMind en el paper AMIE (arXiv:2401.05654) para evaluar agentes de IA clínica.

## 1. Fundamentación

La evaluación de un agente de IA en kinesiología requiere un enfoque estructurado, multidimensional y reproducible. El marco OSCE, ampliamente utilizado en la formación de profesionales de la salud, proporciona la metodología ideal porque:

- **Estandariza** la evaluación de competencias clínicas complejas
- **Descompone** el razonamiento en ejes medibles y rastreables
- **Permite trazabilidad** de fortalezas y debilidades por área
- **Es familiar** para los kinesiólogos evaluadores (usan OSCE en su formación)

KineIA es un agente RAG que basa sus respuestas en fuentes verificadas. La evaluación OSCE mide no solo si la respuesta es correcta, sino **cómo** el agente construye, fundamenta y comunica esa respuesta.

## 2. Los 32 Ejes de Evaluación

Inspirado en los 32 ejes del paper AMIE (que a su vez sigue el formato USMLE Step 2 CS), adaptamos cada dimensión al dominio kinésico:

### 2.1. Anamnesis / Recolección de Datos (6 ejes)

| # | Eje | Descripción | Puntaje 1 | Puntaje 3 | Puntaje 5 |
|---|-----|-------------|-----------|-----------|-----------|
| H1 | **Pertinencia de preguntas** | ¿El agente indaga sobre datos relevantes al caso antes de responder? | No indaga, responde sin contexto | Indaga parcialmente (omite ≥2 datos clave) | Indaga exhaustivamente todos los datos necesarios |
| H2 | **Completitud de la anamnesis** | ¿Cubre antecedentes, mecanismo de lesión, síntomas, tratamientos previos? | Omite ≥3 categorías de anamnesis | Cubre ≥60% de categorías relevantes | Cubre sistemáticamente todas las categorías |
| H3 | **Organización del interrogatorio** | ¿Estructura lógica de las preguntas (general → específico)? | Desordenado, saltos arbitrarios | Secuencia parcialmente lógica | Secuencia clínica impecable (dolor → mecanismo → antecedentes → funcionalidad) |
| H4 | **Identificación de señales de alarma** | ¿Detecta red flags (banderas rojas) y pregunta sobre ellas? | No menciona ni detecta red flags | Menciona red flags pero no profundiza | Identifica, pregunta y actúa sobre red flags (ej: signos de compresión medular) |
| H5 | **Contextualización del paciente** | ¿Considera edad, nivel de actividad, ocupación, deporte? | Respuesta genérica sin adaptación | Adaptación parcial (solo edad) | Adaptación completa al perfil biopsicosocial del paciente |
| H6 | **Uso de escalas validadas** | ¿Solicita o aplica escalas funcionales pertinentes (EVA, Daniels, FIM, Barthel, etc.)? | No menciona escalas | Nombra escalas genéricamente sin detalle | Propone escalas específicas con puntos de corte y referencias |

### 2.2. Diagnóstico / Evaluación (8 ejes)

| # | Eje | Descripción | Puntaje 1 | Puntaje 3 | Puntaje 5 |
|---|-----|-------------|-----------|-----------|-----------|
| D1 | **Precisión diagnóstica** | ¿El diagnóstico kinésico es correcto según la evidencia presentada? | Diagnóstico incorrecto o no pertinente | Diagnóstico parcialmente correcto (aproximado) | Diagnóstico preciso con justificación anatómica y funcional |
| D2 | **Diagnóstico diferencial** | ¿Considera y descarta otras patologías posibles? | No menciona diferenciales | Menciona 1-2 diferenciales sin análisis | Lista ≥3 diferenciales con criterios de descarte |
| D3 | **Razonamiento basado en evidencia** | ¿Fundamenta el diagnóstico en fuentes verificables? | Sin fundamentación ni fuentes | Cita fuentes genéricas sin precisión | Cita fuentes específicas (guías, protocolos, libros) con nivel de evidencia |
| D4 | **Relación anatomofuncional** | ¿Explica la relación entre la estructura anatómica y la disfunción? | No establece relación estructura-función | Relación superficial | Relación detallada con biomecánica y fisiología articular |
| D5 | **Interpretación de estudios complementarios** | ¿Interpreta correctamente Rx, RM, EMG, espirometría, gasometría según aplique? | Interpretación errónea o ausente | Interpretación parcial | Interpretación correcta con parámetros normales/anormales |
| D6 | **Clasificación de gravedad** | ¿Estratifica correctamente la severidad del cuadro? | No clasifica | Clasificación genérica (leve/moderado/severo) | Clasificación con escalas validadas (GOLD, ASIA, GMFCS, etc.) |
| D7 | **Valoración funcional** | ¿Evalúa el impacto en AVD (actividades de la vida diaria)? | No evalúa impacto funcional | Mención superficial de AVD | Análisis detallado por dominio funcional con escalas |
| D8 | **Pronóstico funcional** | ¿Establece pronóstico realista basado en evidencia? | Sin pronóstico o pronóstico infundado | Pronóstico vago sin plazos | Pronóstico con fases temporales, factores modificables y no modificables |

### 2.3. Manejo / Tratamiento (8 ejes)

| # | Eje | Descripción | Puntaje 1 | Puntaje 3 | Puntaje 5 |
|---|-----|-------------|-----------|-----------|-----------|
| M1 | **Adherencia a protocolos** | ¿Sigue guías clínicas oficiales argentinas/internacionales? | No referencia protocolos | Referencia protocolos incorrectamente o desactualizados | Sigue protocolos vigentes (INAREPs, SATI, GOLD, Consenso ACV) con precisión |
| M2 | **Seguridad del paciente** | ¿Considera contraindicaciones, precauciones y criterios de derivación? | Ignora contraindicaciones | Menciona precauciones genéricas | Detalla contraindicaciones absolutas/relativas con fuentes |
| M3 | **Personalización del tratamiento** | ¿Adapta el plan según perfil del paciente (edad, comorbilidades, objetivos)? | Plan genérico sin adaptación | Adaptación superficial (solo edad) | Plan personalizado con justificación para cada adaptación |
| M4 | **Progresión de cargas** | ¿Describe fases con criterios de progresión objetivos? | Sin fases ni criterios | Fases mencionadas sin criterios de avance | Fases con criterios medibles (ROM, fuerza Daniels, test funcionales) |
| M5 | **Dosificación de ejercicios** | ¿Especifica series, repeticiones, intensidad, frecuencia? | Sin dosificación | Dosificación incompleta (solo repeticiones) | Dosificación completa (series × repeticiones × %RM × frecuencia × descanso) |
| M6 | **Uso de agentes físicos** | ¿Indica electroterapia, termoterapia, hidroterapia con parámetros correctos? | No considera o indica incorrectamente | Menciona modalidades sin parámetros | Parámetros precisos (frecuencia, intensidad, tiempo, modo, electrodos) |
| M7 | **Educación terapéutica** | ¿Incluye educación del paciente sobre su condición y autocuidado? | Sin componente educativo | Educación genérica | Educación estructurada: mecanismo lesional, pronóstico, autocuidado, signos de alarma |
| M8 | **Criterios de alta** | ¿Define cuándo finaliza el tratamiento y criterios de return to play/return to work? | Sin criterios de alta | Criterios subjetivos | Criterios objetivos con test funcionales validados y puntos de corte |

### 2.4. Comunicación (6 ejes)

| # | Eje | Descripción | Puntaje 1 | Puntaje 3 | Puntaje 5 |
|---|-----|-------------|-----------|-----------|-----------|
| C1 | **Claridad del lenguaje** | ¿Usa terminología apropiada al modo (estudiante vs. profesional)? | Lenguaje confuso o inapropiado al modo | Mayormente claro, con tecnicismos excesivos en modo estudiante | Claridad perfecta, adapta tecnicismos según el modo |
| C2 | **Empatía y rapport** | ¿Muestra calidez, validación de la preocupación del usuario? | Frío, robótico, no reconoce al interlocutor | Empatía esporádica | Empático, valida la consulta ("Excelente pregunta", "Es una duda muy común en la práctica clínica") |
| C3 | **Valor pedagógico** | ¿La respuesta enseña o solo informa? ¿Incluye ejemplos, analogías, mnemotecnias? | Respuesta puramente informativa | Algún elemento didáctico | Respuesta que enseña: ejemplos clínicos, analogías anatómicas, correlatos prácticos |
| C4 | **Estructura de la respuesta** | ¿Organiza la información con jerarquía clara (títulos, subtítulos, viñetas)? | Texto plano sin estructura | Estructura básica | Estructura profesional con jerarquía visual, tablas cuando aplica, resumen al final |
| C5 | **Manejo del desconocimiento** | ¿Admite cuando no tiene información verificada? | Inventa o alucina información | Responde con información tangencial | Declara explícitamente: "No tengo información verificada sobre este tema en mi base de conocimiento" |
| C6 | **Redirección a fuentes** | ¿Sugiere dónde buscar información complementaria o derivar al profesional adecuado? | No redirige | Sugerencia genérica ("consulte a su médico") | Redirección específica con referencias (guías, sociedades científicas, especialista indicado) |

### 2.5. Integración de Conocimiento (4 ejes)

| # | Eje | Descripción | Puntaje 1 | Puntaje 3 | Puntaje 5 |
|---|-----|-------------|-----------|-----------|-----------|
| K1 | **Citación de fuentes** | ¿Cita fuentes con formato completo y verificable? | Sin citas | Citas incompletas (sin año, sin autor) | Citas completas: Autor(es), Título, Editorial/Revista, Año, Página/Capítulo |
| K2 | **Niveles de evidencia** | ¿Diferencia correctamente entre niveles de evidencia (🟢🔵🟡🟠)? | No diferencia niveles | Diferencia pero con errores | Clasifica correctamente cada fuente según el sistema KineIA |
| K3 | **Contexto argentino** | ¿Referencia normativa, protocolos y práctica clínica argentina? | Ignora el contexto argentino | Mención superficial | Integra guías argentinas (INAREPs, SATI, SAMFYR, Consensos nacionales, Resoluciones ministeriales) |
| K4 | **Actualización del conocimiento** | ¿La información refleja el estado del arte actual (últimos 5 años)? | Información desactualizada (>10 años) | Mayormente actualizada con algunas referencias antiguas | Información actualizada, prioriza fuentes recientes (<5 años), menciona cuando cita fuentes clásicas |

## 3. Metodología de Puntuación

### 3.1. Escala por Eje

Cada eje se puntúa de 1 a 5:

| Puntaje | Significado |
|---------|-------------|
| **1** | **Deficiente**: No demuestra la competencia. Respuesta inadecuada o ausente. |
| **2** | **Insuficiente**: Demuestra la competencia de forma incompleta o con errores significativos. |
| **3** | **Aceptable**: Demuestra la competencia de forma básica. Cumple con lo mínimo esperable. |
| **4** | **Competente**: Demuestra la competencia con solidez. Supera lo mínimo. |
| **5** | **Excelente**: Demuestra maestría. Respuesta ejemplar que podría usarse como material didáctico. |

### 3.2. Puntajes Compuestos

| Dimensión | Ejes | Puntaje máximo | Peso en score global |
|-----------|------|---------------|---------------------|
| Anamnesis | H1-H6 | 30 | 15% |
| Diagnóstico | D1-D8 | 40 | 30% |
| Tratamiento | M1-M8 | 40 | 30% |
| Comunicación | C1-C6 | 30 | 15% |
| Integración | K1-K4 | 20 | 10% |
| **Total** | **32 ejes** | **160** | **100%** |

### 3.3. Interpretación del Score Global

| Rango | Calificación | Interpretación |
|-------|--------------|----------------|
| 145-160 | **Sobresaliente** | Rendimiento de nivel especialista. Listo para uso clínico asistido. |
| 128-144 | **Muy Bueno** | Rendimiento de nivel profesional avanzado. Confiable con supervisión. |
| 96-127 | **Bueno** | Rendimiento de nivel profesional básico. Útil como herramienta de apoyo. |
| 64-95 | **Regular** | Rendimiento de nivel estudiante avanzado. Requiere mejoras significativas. |
| 32-63 | **Insuficiente** | No alcanza el nivel mínimo aceptable. Requiere rediseño del sistema. |

## 4. Formulario de Evaluación

### 4.1. Plantilla por Pregunta

```markdown
## Evaluación OSCE — Pregunta #[número]

**Área**: [área]
**Tema**: [tema específico]
**Dificultad**: [Básico / Intermedio / Avanzado]
**Modo**: [Estudiante / Profesional / Examen]
**Fecha**: [YYYY-MM-DD]
**Evaluador**: [nombre o ID]

### Respuesta de KineIA

[texto completo de la respuesta del agente]

### Fuentes citadas por KineIA

1. [fuente 1]
2. [fuente 2]

### Evaluación por Eje OSCE

| # | Eje | Puntaje (1-5) | Comentario |
|---|-----|:---:|------------|
| H1 | Pertinencia de preguntas | | |
| H2 | Completitud de la anamnesis | | |
| H3 | Organización del interrogatorio | | |
| H4 | Identificación de señales de alarma | | |
| H5 | Contextualización del paciente | | |
| H6 | Uso de escalas validadas | | |
| D1 | Precisión diagnóstica | | |
| D2 | Diagnóstico diferencial | | |
| D3 | Razonamiento basado en evidencia | | |
| D4 | Relación anatomofuncional | | |
| D5 | Interpretación de estudios complementarios | | |
| D6 | Clasificación de gravedad | | |
| D7 | Valoración funcional | | |
| D8 | Pronóstico funcional | | |
| M1 | Adherencia a protocolos | | |
| M2 | Seguridad del paciente | | |
| M3 | Personalización del tratamiento | | |
| M4 | Progresión de cargas | | |
| M5 | Dosificación de ejercicios | | |
| M6 | Uso de agentes físicos | | |
| M7 | Educación terapéutica | | |
| M8 | Criterios de alta | | |
| C1 | Claridad del lenguaje | | |
| C2 | Empatía y rapport | | |
| C3 | Valor pedagógico | | |
| C4 | Estructura de la respuesta | | |
| C5 | Manejo del desconocimiento | | |
| C6 | Redirección a fuentes | | |
| K1 | Citación de fuentes | | |
| K2 | Niveles de evidencia | | |
| K3 | Contexto argentino | | |
| K4 | Actualización del conocimiento | | |
| | **TOTAL** | **/160** | |

### Observaciones cualitativas

[Fortalezas, debilidades, errores detectados, alucinaciones, omisiones]
```

### 4.2. Planilla Resumen (por lote de evaluación)

```markdown
## Resumen OSCE — Lote [nombre]

**Fecha**: [YYYY-MM-DD]
**Total de preguntas**: [N]
**Evaluador(es)**: [nombres]

### Resultados por Área

| Área | N Preguntas | Promedio H | Promedio D | Promedio M | Promedio C | Promedio K | Score Global |
|------|:-----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:------------:|
| Traumatología | | | | | | | |
| Neurología | | | | | | | |
| Respiratorio | | | | | | | |
| Deporte | | | | | | | |
| UCI | | | | | | | |
| Pediatría | | | | | | | |
| Columna | | | | | | | |
| **TOTAL** | | | | | | | |

### Ejes con mejor desempeño (Top 5)
1. 
2. 

### Ejes con peor desempeño (Bottom 5)
1. 
2. 

### Errores sistemáticos detectados
- 

### Recomendaciones
- 
```

## 5. Referencias Metodológicas

- **AMIE (Google DeepMind)**: *"Towards Conversational Diagnostic AI"* — arXiv:2401.05654. Define el marco de 32 ejes OSCE para evaluar agentes de IA clínica. Validado con 20 examinadores OSCE certificados y pacientes simulados.
- **USMLE Step 2 CS**: El examen clínico objetivo estructurado del que deriva la taxonomía de ejes. Evalúa: data gathering (Hx), patient note (Dx), communication skills (Cx).
- **CanMEDS Framework**: Marco de competencias del Royal College of Physicians and Surgeons of Canada. Define los roles: Medical Expert, Communicator, Collaborator, Scholar, Health Advocate, Professional.
- **Consenso ACV Isquémico Agudo**: Revista Medicina Buenos Aires, 2019. Ejemplo de protocolo argentino utilizado como referencia.
- **INAREPs Guía Lesión Medular**: Instituto Nacional de Rehabilitación, 2018. Referencia para evaluación de adherencia a protocolos nacionales.
