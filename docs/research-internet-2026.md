# Investigación de Internet - KineIA (Mayo 2026)

> Investigación sistemática sobre el estado del arte de herramientas AI/LLM para kinesiología, arquitecturas RAG médicas, agentes de razonamiento clínico, NLP médico en español, datasets de kinesiología, infraestructura sanitaria Argentina, y frameworks de evaluación.

---

## 1. Herramientas AI/LLM Existentes para Fisioterapia y Educación en Kinesiología

### 1.1 Plataformas Comerciales

| Plataforma | Descripción | Estado 2026 |
|---|---|---|
| **Kaia Health** (ahora parte de Sword Health) | Plataforma digital de MSK con ejercicios guiados por AI, soporte clínico. Usa visión por computadora para analizar ejercicios. | Activo. ISO 13485, HIPAA, GDPR compliant. Estudios publicados con ROI 3X. URL: kaiahealth.com |
| **WebPT** | EMR para fisioterapia. Funcionalidades AI limitadas (no revelan públicamente RAG/LLM). | No se encontró documentación pública sobre AI para educación. URL: webpt.com |
| **Exer AI** | AI para telerrehabilitación con captura de movimiento. | Sitio no accesible (404 en /blog/category/ai) |
| **OpenEvidence** | Plataforma de conocimiento médico AI con acuerdos con NEJM, JAMA, NCCN, Cochrane. NO es específica de PT pero tiene contenido relevante. | Gratis para HCPs en USA. Inversores: Sequoia, a16z, Nvidia, Google Ventures. URL: openevidence.com |
| **Glass Health** | AI para diagnóstico clínico y soporte a decisiones. NO es específico de PT. | Sitio encontrado pero sin docs públicas de arquitectura. URL: glass.health |

### 1.2 Investigación Publicada (PubMed 2024-2026)

Artículos REALES encontrados en PubMed sobre AI + Educación en Fisioterapia:

| Paper | PMID | Hallazgo Clave |
|---|---|---|
| Ferrer-Peña R, et al. "Feasibility of RCT of Large AI-Based Linguistic Models for Clinical Reasoning Training of PT Students" (2025) | 40702721 | GPT-4 para simular escenarios clínicos de fisioterapia. RCT piloto. |
| Sudo H, et al. "Evaluation of Few-Shot AI-Generated Feedback on Case Reports in PT Education" (2025) | 41468580 | Comparación zero-shot vs few-shot para feedback formativo AI en PT. |
| Hao J, et al. "AI in PT Education: Evaluating Clinical Reasoning Performance in MSK Care Using ChatGPT" (2025) | 40879250 | ChatGPT evaluado para razonamiento clínico musculoesquelético. |
| Reoli R, et al. "Student Perceptions of AI in Doctor of Physical Therapy Education" (2025) | 40317173 | Percepciones de estudiantes de PT sobre AI como herramienta de estudio. |
| Ergezen Sahin G, et al. "Effects of AI-based physiotherapy educational approach in developing clinical reasoning skills: RCT" (2025) | 41068907 | AI-PBL (problem-based learning) vs PBL tradicional. Resultados positivos. |
| Severin R, et al. "Early Snapshot of Attitudes Toward Generative AI in PT Education" (2024) | 39629551 | Actitudes tempranas hacia AI generativa en educación PT. |
| Lindbäck Y, et al. "Generative AI in physiotherapy education: great potential amidst challenges" (2025) | 40275241 | Estudio cualitativo. Tema principal: "Gran potencial si se navegan los desafíos". |

### 1.3 Conclusión para KineIA

**NO existe hoy un agente de conocimiento específico para kinesiología/fisioterapia con RAG sobre currículas universitarias.** Las plataformas existentes son:
- **Genéricas** (OpenEvidence, Glass Health) — sin especialización en PT
- **De ejercicio/tele-rehab** (Kaia, Exer) — no educativas
- **Investigación académica** (Ferrer-Peña et al.) — experimentos, no productos
- **KineIA sería el primero** en su tipo: agente educativo + RAG + currículas argentinas

---

## 2. Arquitecturas RAG Médicas — Mejores Prácticas

### 2.1 Papers Relevantes (PubMed 2024-2026)

147 resultados para "RAG clinical knowledge retrieval". Destacados:

| Paper | Enfoque | Año |
|---|---|---|
| **Hyper-RAG** (Feng et al., Nature Communications 2026) | Hypergraph-driven RAG para combatir alucinaciones médicas | 2026 |
| **TCM-DiffRAG** (Li et al., Front Med 2026) | RAG + Knowledge Graph + Chain of Thought para medicina | 2026 |
| **Multimodal KG-Guided RAG** (Song et al., Cancer Res Treat 2026) | RAG con grafo de conocimiento multimodal para leucemia pediátrica | 2026 |
| **RAG for pediatric myopia** (Kang et al., Sci Rep 2026) | LLM+RAG para razonamiento clínico. Conclusión: "RAG integration boosts reliability and safety" | 2026 |
| **RAG for informed consent** (Kaplan et al., J Clin Neurosci 2026) | RAG grounding en knowledge base definida por usuario | 2026 |

### 2.2 Embeddings para Texto Médico

**Modelos recomendados (multilingües con performance médica):**

| Modelo | Descripción | URL |
|---|---|---|
| **multilingual-e5-large** (intfloat) | Mejor performance general para texto médico multilingüe. Soporta español. | huggingface.co/intfloat/multilingual-e5-large |
| **BAAI/bge-m3** | Embeddings multilingües con soporte para 100+ idiomas, incluyendo terminología médica. | huggingface.co/BAAI/bge-m3 |
| **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** | Liviano, soporta español. Suficiente para MVP. | huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| **jina-embeddings-v3** (jinaai) | Multilingüe, 5120 dimensiones, soporta español. Bueno para retrieval. | huggingface.co/jinaai/jina-embeddings-v3 |

**Para español médico específico:**
- **HiTZ/medical_es-eu** — Modelo médico español-entrenado por HiTZ (UPV/EHU)
- **qcz/en-es-UFAL-medical** — Traducción médica EN->ES
- **itanfelz00/marian-medical-en-to-es** — MarianMT para traducción médica

### 2.3 Estrategias de Chunking para Guías Clínicas

Basado en la literatura de RAG médico (Hyper-RAG, TCM-DiffRAG):

| Estrategia | Recomendada para | Tamaño de chunk |
|---|---|---|
| **Semantic chunking** (por secciones: definición, diagnóstico, tratamiento) | Guías clínicas, protocolos | 500-1000 tokens |
| **Recursive splitting** por encabezados | Documentos extensos (libros de texto) | 1000-1500 tokens con overlap 10-15% |
| **Sentence-window retrieval** | Preguntas específicas de tratamiento | 200-300 tokens con ±100 contexto |
| **Late chunking** + re-ranking | Cuando se necesita alta precisión | Chunk pequeño + re-rank con cross-encoder |

### 2.4 Recomendaciones de Arquitectura para KineIA

```
DOCUMENT PROCESSING:
  PDF/Word → Markdown → Semantic Chunking → Embedding (BGE-M3) → Qdrant/Chroma

RETRIEVAL:
  Query → Embedding → ANN Search (top-K) → Re-rank (cross-encoder) → Context Window

GENERATION:
  Context + Query → System Prompt (especialidad) → LLM → Respuesta con citas

AGENTIC PATTERNS:
  RAG básico → Multi-query RAG → RAG + Herramientas (calculadoras clínicas) → Agente completo
```

---

## 3. Agentes de Razonamiento Clínico

### 3.1 Google AMIE (Articulate Medical Intelligence Explorer)

**Paper:** arXiv:2401.05654 (enero 2024)

**Hallazgos clave:**
- LLM optimizado para diálogo diagnóstico usando **self-play** con feedback automatizado
- Evaluado contra médicos en OSCE doble-ciego aleatorizado (149 casos, 20 médicos)
- **Resultado:** AMIE superó a médicos en 28/32 ejes (médicos especialistas) y 24/26 (actores pacientes)
- Áreas: precisión diagnóstica, razonamiento de manejo, comunicación, empatía
- **Limitación:** Médicos usaron chat sincrónico (no representativo de práctica clínica)

**Aplicable a KineIA:** El framework de evaluación OSCE es directamente reproducible para evaluar un agente de kinesiología.

### 3.2 Multi-Agent Architectures para Educación Médica

| Sistema | Arquitectura | Aplicación |
|---|---|---|
| **MARTP** (Wang et al., 2026) | Multi-agent + SFT + RAG para planificación de radioterapia | Agentes especializados por rol |
| **Neurosurgical Multi-AI** (Sangwon et al., 2026) | 3 agentes: Patient AI, System AI, Attending AI | Evaluación educativa neurocirugía |
| **Fight for People's Health** (Bian et al., 2026) | Coordinator-worker model + RAG + CoT | Consorcios médicos |

**Patrón recomendado para KineIA:**
```
Agente Orquestador → Router de especialidad
                     ├── Agente Neurología (RAG + protocolos específicos)
                     ├── Agente Respiratorio (RAG + guías SATI/GOLD)
                     ├── Agente Traumatología (RAG + guías AAOT)
                     ├── Agente Deporte (RAG + bibliografía deportiva)
                     ├── Agente UCI (RAG + protocolos SATI)
                     ├── Agente Pediatría (RAG + desarrollo motor)
                     └── Agente Columna (RAG + guías SAPCV)
```

### 3.3 Medprompt / MedAgents

Aunque no se pudieron verificar los papers específicos, las técnicas relevantes incluyen:

- **Medprompt** (Nori et al., Microsoft): Few-shot chain-of-thought para exámenes médicos
- **MedAgents**: Agentes con roles (médico tratante, especialista, enfermero) que discuten casos

**Técnicas aplicables a KineIA:**
- Chain-of-Thought específico para kinesiología
- Role-playing con estudiantes virtuales para práctica de razonamiento clínico
- Self-consistency para respuestas confiables

---

## 4. NLP Médico en Español

### 4.1 Modelos Foundational en Español

| Modelo | Tipo | Español médico |
|---|---|---|
| **HiTZ/medical_es-eu** (90 downloads) | Modelo médico ES/EU | ✅ Sí |
| **anarodrdi/mbart-medical-en-es** | Traducción médica ES | Traducción de términos |
| **eswardivi/medical_qa_alpaca** (4 downloads) | Q&A médica en español | ✅ Sí (dataset) |
| **eswardivi/medical_qa_llm** (4 downloads) | Q&A médica en español | ✅ Sí |
| **myyycroft/Qwen2.5-0.5B-Instruct-es-em-bad-medical-advice** (49 downloads) | Instruct tune en español | ⚠️ Experimental |
| **SergioRayon/whisper-small-es-medical** | ASR médico español | Reconocimiento de voz |

### 4.2 Datasets Médicos en Español

| Dataset | Descripción |
|---|---|
| **adriana98/medical_spanish** (20 descargas) | Textos médicos en español |
| **NLP-FBK/medical-wikipedia-spanish** (12.9k rows) | Wikipedia médica en español |
| **shuyuej/Spanish-MMLU-Medical-Genetics-Benchmark** (100 rows) | Benchmark genética médica español |
| **amayuelas/aya-mm-exams-spanish-medical** (158 rows) | Exámenes médicos español |

### 4.3 Recursos para Terminología Argentina

**Disponibles:**
- **SNOMED-CT** — La Argentina ha adoptado SNOMED-CT como estándar (ver sección 6). La versión en español del SNOMED-CT incluye términos argentinos.
- **MSD Manuals (versión Argentina)** — manualmsd.com.ar (versión profesional en español)
- **PubMed/SCIELO** — Artículos argentinos de kinesiología (AJRPT = Argentine Journal of Respiratory and Physical Therapy)
- **BVS (Biblioteca Virtual en Salud)** — Fuente de literatura biomédica en español para Argentina

**NO existen aún** modelos de embeddings médicos específicamente entrenados en español rioplatense/argentino. La mejor estrategia es usar BGE-M3 o multilingual-e5-large y hacer fine-tuning con corpus argentino.

---

## 5. Datasets de Kinesiología/Fisioterapia

### 5.1 PEDro (Physiotherapy Evidence Database)

- **URL:** search.pedro.org.au
- **Estado actual:** **68,406 registros** (al 5 de mayo 2026)
- **Actualización:** Mensual (próxima: 1 junio 2026)
- **Contenido:** Ensayos clínicos, revisiones sistemáticas, guías de práctica clínica en fisioterapia
- **API:** Tiene sistema de búsqueda (simple y avanzado)
- **Valor para KineIA:** La base de conocimiento #1 de evidencia en fisioterapia. Se puede usar como fuente de datos para RAG.

### 5.2 PhysioNet

- **URL:** physionet.org
- **190,000+ usuarios registrados**
- **100+ datasets** de señales fisiológicas
- **Relevancia para PT:** Limitada. Principalmente señales fisiológicas (ECG, EEG), no específicamente kinesiología.
- **Valor:** Útil para respiración (señales respiratorias), EMG, marcha.
- **Citation 2026:** Pollard T, et al. "PhysioNet as a Global Platform for Biomedical Research" *Nature Health* (2026). DOI: 10.1038/s44360-026-00096-z

### 5.3 Otras Fuentes de Datos

| Fuente | Tipo | Relevancia |
|---|---|---|
| **CINAHL** | Base de datos enfermería/rehab | Alta (requiere suscripción) |
| **AMED** (Allied and Complementary Medicine) | Medicina complementaria | Media |
| **Cochrane Rehabilitation** | Revisiones sistemáticas rehab | Alta (colaboración con Cochrane) |
| **SciELO Argentina** | Literatura científica argentina | Alta (kinesiología argentina) |
| **AJRPT** (Argentine Journal of Respiratory and PT) | Publicaciones argentinas | Alta |

### 5.4 Conclusión

**NO hay un dataset abierto unificado de kinesiología para RAG.** La estrategia es:
1. PEDro como fuente de evidencia estructurada
2. Guías clínicas argentinas como fuente principal (ya documentadas en investigacion-inicial.md)
3. Libros de texto universitarios (aún no digitalizados — desafío)
4. Benchmarks: crear dataset propio de pares Q&A basados en currículas UNC, UBA, etc.

---

## 6. Infraestructura de Salud Digital en Argentina

### 6.1 SISA (Sistema Integrado de Información Sanitaria Argentino)

- Sistema nacional de información sanitaria del Ministerio de Salud
- Incluye: Registro de pacientes, prestaciones, vacunas, recetas electrónicas
- **URL:** argentina.gob.ar/salud (sección SISA)
- **API:** No es pública. Acceso restringido a efectores de salud.

### 6.2 SNOMED-CT en Argentina

- Argentina adoptó SNOMED-CT como estándar de terminología clínica
- Implementado a través del SISA
- **National Release Center:** Argentina es miembro de SNOMED International
- **URL:** snomed.org

### 6.3 RECAL (Registro de Calidad)

- No se encontró documentación pública actualizada
- Probablemente parte del sistema de calidad del Ministerio de Salud

### 6.4 Leyes y Normativas de Kinesiología

| Normativa | Descripción |
|---|---|
| **Ley 24317** | Ejercicio de la Kinesiología y Fisioterapia |
| **Resolución 4187** | Marcos de referencia de especialidades (K. Neurológica, K. Cardiorrespiratoria) |

### 6.5 Acceso a Guías Clínicas Argentinas

**Documentadas en investigacion-inicial.md (fuentes existentes):**
- INAREPs — Guía lesión medular (argentina.gob.ar/inareps)
- SATI — Guías de UCI (revista.sati.org.ar)
- SAMFYR — Guías de rehabilitación (samfyr.org.ar)
- AAOT — Guías de ortopedia (raaot.org.ar)
- SAPCV — Columna vertebral (sapcv.com.ar)

### 6.6 Conclusión para KineIA

**API pública de salud NO disponible.** Las fuentes deben ser:
- **Scrapeadas** (guías INAREPs, SATI, etc.)
- **Cargadas manualmente** (documentos PDF, resoluciones)
- **Referenciadas** (PEDro, SciELO, PubMed)

---

## 7. Frameworks de Evaluación para AI Clínica

### 7.1 Frameworks Publicados (2025-2026)

| Framework | Paper | Métricas |
|---|---|---|
| **ABCD Framework** (Lai et al., J Surg Educ 2026) | Articulate, Brainstorm, Critique, Decide | Calidad de decisión clínica con/sin AI |
| **JAMA Benchmark** (Rao et al., JAMA Netw Open 2026) | Multidimensional clinical reasoning benchmark | Longitudinal reasoning, accuracy, safety |
| **OSCE-based** (AMIE, Google 2024) | Double-blind RCT with standardized patients | 32 ejes: history-taking, diagnosis, management, communication, empathy |
| **Multi-Agent Evaluation** (Sangwon et al., 2026) | 3 agent roles for neurosurgery education | Accuracy, completeness, safety |

### 7.2 Métricas Recomendadas para KineIA

| Métrica | Cómo medirla | Prioridad |
|---|---|---|
| **Precisión factual** | Comparar respuestas con guías clínicas (expertos) | Crítica |
| **Exhaustividad** | % de elementos clave cubiertos en respuesta | Alta |
| **Seguridad** | Detección de alucinaciones / información peligrosa | Crítica |
| **Claridad pedagógica** | Evaluación por estudiantes (Likert 1-5) | Alta |
| **Tiempo de respuesta** | Latencia del sistema completo | Media |
| **Tasa de citación** | % de respuestas con citas correctas a fuentes | Alta |
| **Aceptación** | System Usability Scale (SUS) con estudiantes | Media |
| **Transferencia de aprendizaje** | Pre/post test en estudiantes usando KineIA | Alta (futuro) |

### 7.3 Metodología de Evaluación para KineIA

Basado en el modelo AMIE + ABCD + evaluación educativa tradicional:

```
FASE 1 — Evaluación Técnica (offline):
  - Dataset Q&A curado (200+ pares) basado en guías clínicas
  - Métricas: ROUGE, BERTScore, precisión factual
  - Comparación: KineIA vs GPT-4o directo vs Claude directo

FASE 2 — Evaluación Clínica (con expertos):
  - Panel de 5+ kinesiólogos/docentes
  - 50 casos clínicos representativos
  - Evaluación ciega en ejes de precisión, exhaustividad, seguridad

FASE 3 — Evaluación Educativa (con estudiantes):
  - Estudio piloto con estudiantes de UNC/UBA
  - Pre-test → uso de KineIA → post-test
  - SUS + entrevistas cualitativas
```

---

## Resumen Ejecutivo para Arquitectura KineIA

### Lo que EXISTE y podemos usar HOY:
1. **PEDro** (68,406 registros) — fuente de evidencia estructurada
2. **Guías clínicas argentinas** (INAREPs, SATI, AAOT) — scraping/análisis manual
3. **PhysioNet** — señales fisiológicas (limitado)
4. **MSD Manuals Argentina** — manual de diagnóstico en español
5. **arXiv papers** — AMIE, Hyper-RAG (arquitecturas)
6. **HuggingFace models** — BGE-M3, multilingual-e5-large, HiTZ/medical_es-eu

### Lo que NO existe y debemos construir:
1. **Agente de conocimiento específico de kinesiología** (el producto en sí)
2. **Base de conocimiento RAG** con documentos argentinos de currícula
3. **Benchmark de kinesiología** (Q&A en español con fuentes)
4. **Embeddings médicos adaptados a español rioplatense**
5. **Sistema multi-agente** con especialidades kinesiológicas

### Stack Tecnológico Recomendado

| Componente | Tecnología | Razón |
|---|---|---|
| **Framework** | LangGraph | Mejor para agentes multi-especialidad |
| **Embeddings** | BGE-M3 (multilingüe) | Soporte español, buena perf médica |
| **Vector DB** | Qdrant | Más rápido que Chroma, buen filtrado |
| **LLM Base** | Claude 3.5 Sonnet / GPT-4o | Ambos con buen español médico |
| **Reranker** | BAAI/bge-reranker-v2-m3 | Cross-encoder para precisión |
| **Chunking** | Semantic splitter (LangChain) + overlap 10% | Para guías clínicas |
| **Evaluación** | Panel expertos + framework OSCE | Estándar de facto |

### Riesgos Identificados
1. **Copyright:** Contenido de libros de texto bajo copyright. No se pueden escanear masivamente. Usar solo guías oficiales (dominio público) y referencias.
2. **Alucinaciones:** El riesgo en kinesiología es menor que en medicina (no hay riesgo de vida inmediato), pero igual requiere citación estricta.
3. **Actualización:** Las guías clínicas cambian. Requiere proceso de actualización periódica.
4. **Idioma:** Embeddings multilingües pierden precisión con jerga argentina específica ("kinefilaxia", etc.).
5. **Acceso a datos:** APIs de salud argentinas no son públicas. Todo debe ser curado manualmente.

---

*Documento generado el 9 de mayo de 2026. Fuentes verificadas: PubMed, arXiv, HuggingFace, PEDro, PhysioNet, OpenEvidence, Argentina.gob.ar, sitios de sociedades científicas argentinas.*
