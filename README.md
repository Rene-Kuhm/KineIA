# KineIA 🧠💪

**Agente de Inteligencia Artificial para Kinesiología**

KineIA es un agente de conocimiento EXPERTO en kinesiología basado en currículas universitarias argentinas, protocolos clínicos oficiales, guías de práctica clínica, consensos de sociedades científicas y libros de texto fundamentales.

## 🎯 Objetivo

Servir como asistente de conocimiento para estudiantes, graduados y profesionales de kinesiología, respondiendo consultas basadas en evidencia científica y bibliografía oficial.

## 🚀 Estado del Proyecto

| Fase | Estado |
|------|--------|
| Investigación inicial | ✅ Completa |
| SDD (Propuesta + Especificaciones + Diseño) | ✅ Completo |
| Backend (FastAPI + RAG + Qdrant) | 🟡 85% — funcional, mejoras en curso |
| Frontend (Next.js 15 + Chat UI) | 🟡 70% — chat funcional, admin pendiente |
| Knowledge Base (54 documentos) | ✅ Indexados en Qdrant |
| Testing | 🔴 Pendiente |
| Deploy | 🔴 Pendiente |

## 🛠️ Tech Stack

| Componente | Tecnología |
|---|---|
| **Backend** | FastAPI (Python 3.12), async |
| **Vector DB** | Qdrant (self-hosted) |
| **Database** | PostgreSQL 16 (users, conversations) |
| **LLM** | Groq (Llama 3.3 70B) / Anthropic (Claude 3.5 Sonnet) |
| **Embeddings** | BGE-M3 (multilingual, 1024d) |
| **RAG** | LangChain + custom retrieval + reranker |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS 4 |
| **Infra** | Docker Compose (4 services) |

## 📂 Estructura

```
KineIA/
├── backend/           # FastAPI + RAG pipeline
│   ├── app/
│   │   ├── api/v1/    # Chat, Search, Auth, Knowledge endpoints
│   │   ├── core/      # RAG, Ingestion, LLM, Auth logic
│   │   ├── models/    # SQLAlchemy models
│   │   ├── services/  # Business logic
│   │   └── db/        # PostgreSQL + Qdrant connections
│   └── tests/         # Pytest (en construcción)
├── frontend/          # Next.js Chat UI
│   └── src/
│       ├── app/       # Pages (layout, chat)
│       ├── components/ # ChatWindow, MessageBubble, SourceCard, ModeSelector
│       └── lib/       # API client, utils
├── knowledge_base/    # 54 documentos en 7 categorías
│   ├── anatomia/
│   ├── guias-clinicas/
│   ├── libros/        # 19 libros de referencia
│   ├── normativa/
│   ├── papers/
│   ├── protocolos/    # 12 protocolos clínicos
│   └── universidades/
├── docs/              # SDD + investigación
│   └── sdd/           # Proposal, Spec, Design, Tasks
├── scripts/           # seed-knowledge.py
└── docker-compose.yml
```

## 🏃 Quick Start

```bash
# 1. Clonar
git clone https://github.com/Rene-Kuhm/KineIA.git
cd KineIA

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Levantar servicios
docker compose up -d

# 4. Sembrar la base de conocimiento
docker compose exec backend python scripts/seed-knowledge.py

# 5. Abrir frontend
open http://localhost:3000
```

## 📚 Fuentes de Conocimiento

### Universidades Documentadas
- UNC Córdoba (5 años, 25 asignaturas)
- UBA (6 años, 30 asignaturas)
- UNSL (5 años)
- UNLaM (5 años)
- Favaloro (5 años, 1600+hs prácticas)

### Áreas de Especialización
- Neurología (ACV, lesión medular, Parkinson, EM)
- Respiratorio (EPOC, VM, rehab pulmonar, UCI)
- Traumatología (fracturas, prótesis, columna, cadera)
- Deporte (lesiones musculares, tendones, return to play)
- UCI (ventilación mecánica, extubación, disfagia)
- Pediátrico (desarrollo motor, DCD, parálisis cerebral)
- Columna (hernia discal, dolor lumbar, escoliosis)

### Protocolos Clínicos Oficiales (Argentina)
- INAREPs - Guía lesión medular (2018)
- Consenso ACV - Revista Medicina 2019
- CISFraCAM 2021 - Fractura cadera
- Resolución 4187 - Marcos de referencia especialidades
- Guía GOLD 2024 - EPOC

### Sociedades Científicas
- SATI (Terapia Intensiva)
- SAMFYR (Medicina Física y Rehabilitación)
- SAPCV (Patología de la Columna)
- AAOT (Ortopedia y Traumatología)

## 🔬 Evidencia

7 papers en PubMed (2024-2026) validan el uso de AI + LLMs para educación en fisioterapia. Dos RCTs muestran resultados positivos:
- Ferrer-Peña et al. (2025, PMID: 40702721): GPT-4 para razonamiento clínico en PT
- Ergezen et al. (2025, PMID: 41068907): AI-PBL supera PBL tradicional

Ver `docs/research-internet-2026.md` para la investigación completa.

## 📖 Licencia

MIT License

## 👤 Autor

Desarrollado con ❤️ para la comunidad kinesiológica argentina
