# KineIA - Propuesta Técnica (SDD)

## 1. Intent (Intención)

Crear un agente de IA EXPERTO en kinesiología que sirva como asistente de conocimiento para estudiantes, graduados y profesionales de kinesiología en Argentina, respondiendo consultas basadas en evidencia científica, bibliografía oficial y protocolos clínicos reales.

## 2. Problem Statement (Problema)

Los estudiantes y profesionales de kinesiología en Argentina:
- No tienen un punto centralizado de consulta con información verificada
- Dependen de múltiples fuentes dispersas (Filadd, Wuolah, PDFs sueltos)
- No acceden fácilmente a protocolos clínicos oficiales del gobierno
- Necesitan respuestas basadas en evidencia, no en opiniones
- Buscan material de estudio para exámenes y práctica clínica

## 3. Proposed Solution (Solución Propuesta)

### Arquitectura RAG (Retrieval Augmented Generation)

Un agente conversacional que:
1. **Indexa** libros, guías clínicas, protocolos, papers y apuntes en una base vectorial
2. **Busca** información relevante ante cada consulta del usuario
3. **Genera** respuestas precisas citando fuentes reales
4. **Diferencia** entre niveles de evidencia (protocolo oficial vs. apunte estudiantil)

### Stack Técnico Propuesto

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| **Backend** | Python (FastAPI) | Ecosistema ML maduro, async, rápido |
| **Framework IA** | LangChain / LangGraph | Orquestación de agentes, herramientas, RAG |
| **Vector DB** | Qdrant | Open-source, self-hosted, rápido, filtros avanzados |
| **LLM** | Claude 3.5 Sonnet (primario) / Ollama (fallback local) | Calidad de respuesta + opción self-hosted |
| **Embeddings** | all-MiniLM-L6-v2 (sentence-transformers) | Gratuito, rápido, buena calidad en español |
| **Frontend** | Next.js 15 / React | UI moderna, SSR, responsive |
| **Base de datos** | PostgreSQL | Metadata, usuarios, historial |
| **Infra** | Docker + Docker Compose | Deploy en VPS |

## 4. Scope (Alcance)

### In Scope (Dentro del alcance):
- Chat conversacional con RAG
- Búsqueda semántica en base de conocimiento
- Respuestas con citación de fuentes
- Diferenciación por nivel de evidencia
- Soporte para estudiantes (preguntas de examen, material de estudio)
- Soporte para profesionales (protocolos clínicos, guías de práctica)
- Interface web responsive
- Deploy en VPS (Docker)

### Out of Scope (Fuera del alcance - v1):
- App mobile nativa
- Integración con sistemas hospitalarios
- Generación de diagnósticos (responsabilidad médica)
- Integración con LMS universitarios
- Multi-idioma (solo español v1)

## 5. Success Criteria (Criterios de Éxito)

1. El agente responde correctamente el 90%+ de preguntas de exámenes de kinesiología UNC
2. Cita fuentes verificables en cada respuesta
3. Tiempo de respuesta < 5 segundos
4. Diferencia correctamente entre niveles de evidencia
5. Funciona 24/7 en la VPS

## 6. Risks (Riesgos)

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Calidad de embeddings en español | Media | Alto | Probar múltiples modelos, fine-tune si necesario |
| Acceso a PDFs de libros | Alta | Alto | Usar fuentes abiertas, complementar con resúmenes |
| Alucinaciones del LLM | Media | Alto | RAG estricto, system prompt con restricciones, citación obligatoria |
| Recursos de VPS (4GB RAM) | Media | Medio | Optimizar, usar Ollama con modelos pequeños o API externa |
| Derechos de autor de libros | Alta | Alto | Solo indexar resúmenes, citas, no texto completo |

## 7. Timeline Estimado

| Fase | Descripción |
|------|-------------|
| **Fase 1** | Setup proyecto + Base de datos vectorial + Ingesta de documentos |
| **Fase 2** | Pipeline RAG + LLM integration + Chat básico |
| **Fase 3** | Frontend web + UI conversacional |
| **Fase 4** | Deploy en VPS + Testing + Optimización |

## 8. Knowledge Base Structure (Estructura de la Base de Conocimiento)

### Colecciones de documentos:

```
knowledge_base/
├── universidades/
│   ├── unc/
│   │   ├── plan-estudios.md
│   │   ├── materias/
│   │   │   ├── anatomia.md
│   │   │   ├── fisiologia.md
│   │   │   ├── biomecanica.md
│   │   │   └── ...
│   │   ├── examenes/
│   │   ├── docentes/
│   │   └── posgrados/
│   ├── uba/
│   ├── unsl/
│   ├── favaloro/
│   └── unlam/
├── libros/
│   ├── anatomia/
│   │   ├── kapandji-fisiologia-articular.md
│   │   ├── latarjet-anatomia.md
│   │   └── grays-anatomy.md
│   ├── fisiologia/
│   │   ├── guyton.md
│   │   └── costanzo.md
│   ├── biomecanica/
│   │   ├── neumann.md
│   │   └── hamill.md
│   ├── neurologia/
│   │   ├── umphred.md
│   │   └── lundy-ekman.md
│   ├── respiratorio/
│   │   └── krenek.md
│   ├── traumatologia/
│   │   └── egol.md
│   └── deporte/
│       └── salom.md
├── protocolos/
│   ├── lesion-medular-inareps-2018.md
│   ├── consenso-acv-2019.md
│   ├── cisfracam-2021.md
│   ├── gold-epoc-2024.md
│   ├── marco-kinesiologia-neurologica.md
│   └── marco-kinesiologia-cardiorrespiratoria.md
├── guias-clinicas/
│   ├── neurologia/
│   ├── respiratorio/
│   ├── traumatologia/
│   ├── deporte/
│   └── pediatrico/
├── papers/
│   ├── argentina/
│   └── internacional/
└── normativa/
    ├── ley-24317.md
    └── resolucion-4187.md
```

### Metadata por documento:

```json
{
  "source": "Kapandji - Fisiología Articular",
  "type": "libro",
  "area": "anatomia",
  "nivel_evidencia": "referencia_academica",
  "universidad": "UNC",
  "materia": "Anatomía Normal",
  "año_publicacion": 2006,
  "editorial": "Panamericana",
  "tags": ["anatomía", "articulaciones", "biomecánica"]
}
```

## 9. Approval

- [ ] Propuesta aprobada por el usuario
- [ ] Stack técnico confirmado
- [ ] Alcance definido
