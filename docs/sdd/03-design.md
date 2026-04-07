# KineIA - Diseño Técnico

## 1. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                    Next.js 15 (React 19)                        │
│         Chat UI + Dashboard + Panel Admin                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────────┐
│                         BACKEND                                 │
│                    FastAPI (Python 3.12)                         │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Auth     │  │ Chat     │  │ Search   │  │ Knowledge    │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Ingest Svc   │   │
│  └──────────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│                     │             │                │            │
│              ┌──────▼─────────────▼────────────────▼──────┐     │
│              │         RAG Pipeline (LangChain)           │     │
│              │                                            │     │
│              │  Query → Embed → Search → Rerank → LLM    │     │
│              └──────────────────┬─────────────────────────┘     │
│                                │                                │
└────────────────────────────────┼────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐  ┌──────────▼──────────┐  ┌─────────▼────────┐
│   Qdrant        │  │   PostgreSQL        │  │   LLM Provider   │
│   Vector DB     │  │   Metadata + Users  │  │                  │
│   Port: 6333    │  │   Port: 5432        │  │  Claude API      │
│                 │  │                     │  │  OR Ollama local  │
└─────────────────┘  └─────────────────────┘  └──────────────────┘
```

## 2. Estructura del Proyecto

```
KineIA/
├── docker-compose.yml          # Orquestación de servicios
├── .env.example                # Variables de entorno
├── README.md
├── docs/
│   ├── sdd/                    # Documentación SDD
│   └── investigacion-inicial.md
│
├── backend/                    # FastAPI Backend
│   ├── Dockerfile
│   ├── pyproject.toml          # Dependencies (uv/poetry)
│   ├── app/
│   │   ├── main.py             # FastAPI app entry
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── chat.py     # Chat endpoints
│   │   │   │   ├── search.py   # Search endpoints
│   │   │   │   ├── auth.py     # Auth endpoints
│   │   │   │   └── knowledge.py # Knowledge management
│   │   │   └── deps.py         # Dependencies injection
│   │   ├── core/
│   │   │   ├── rag/
│   │   │   │   ├── pipeline.py     # RAG pipeline principal
│   │   │   │   ├── retriever.py    # Búsqueda vectorial
│   │   │   │   ├── reranker.py     # Re-ranking de resultados
│   │   │   │   └── prompts.py      # System prompts del agente
│   │   │   ├── ingestion/
│   │   │   │   ├── pipeline.py     # Pipeline de ingesta
│   │   │   │   ├── chunker.py      # Chunking de documentos
│   │   │   │   ├── embedder.py     # Generación de embeddings
│   │   │   │   └── extractors/
│   │   │   │       ├── pdf.py      # Extractor PDF
│   │   │   │       ├── markdown.py # Extractor Markdown
│   │   │   │       └── text.py     # Extractor texto
│   │   │   └── llm/
│   │   │       ├── provider.py     # LLM provider (Claude/Ollama)
│   │   │       └── chains.py       # LangChain chains
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   └── document.py
│   │   ├── db/
│   │   │   ├── postgres.py     # PostgreSQL connection
│   │   │   └── qdrant.py       # Qdrant connection
│   │   └── utils/
│   │       ├── security.py     # JWT, hashing
│   │       └── evidence.py     # Evidence level classification
│   └── tests/
│       ├── test_chat.py
│       ├── test_search.py
│       └── test_ingestion.py
│
├── frontend/                   # Next.js Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx        # Landing page
│   │   │   ├── chat/
│   │   │   │   └── page.tsx    # Chat interface
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx    # User dashboard
│   │   │   └── admin/
│   │   │       └── page.tsx    # Admin panel
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── SourceCard.tsx
│   │   │   │   └── ModeSelector.tsx
│   │   │   └── ui/             # Shared UI components
│   │   └── lib/
│   │       ├── api.ts          # API client
│   │       └── auth.ts         # Auth utilities
│   └── tailwind.config.ts
│
├── knowledge_base/             # Documentos fuente
│   ├── universidades/
│   ├── libros/
│   ├── protocolos/
│   ├── guias-clinicas/
│   ├── papers/
│   └── normativa/
│
└── scripts/
    ├── seed-knowledge.py       # Script para poblar la base
    ├── backup.sh               # Backup script
    └── deploy.sh               # Deploy script
```

## 3. RAG Pipeline (Detalle)

### 3.1 Ingesta de Documentos

```
Documento (PDF/MD/TXT)
    │
    ▼
┌──────────────┐
│  Extractor   │  → Detecta formato, extrae texto
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Chunker     │  → Divide en chunks de ~512 tokens
│              │    Respeta headers, párrafos, tablas
│              │    Overlap de 50 tokens
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Metadata    │  → Extrae: autor, área, tipo, año
│  Extractor   │    Asigna nivel de evidencia
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Embedder    │  → sentence-transformers (all-MiniLM-L6-v2)
│              │    Genera vector de 384 dimensiones
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Qdrant      │  → Almacena vector + payload (metadata)
│  Upsert      │
└──────────────┘
```

### 3.2 Pipeline de Consulta

```
Pregunta del usuario
    │
    ▼
┌──────────────┐
│  Query       │  → Analiza la pregunta
│  Analyzer    │    Detecta: área, intent, modo
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Embedder    │  → Genera embedding de la pregunta
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Retriever   │  → Busca top-K chunks relevantes en Qdrant
│  (Qdrant)    │    Aplica filtros (área, tipo, universidad)
│              │    K = 10
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Reranker    │  → Re-ordena por relevancia real
│              │    Prioriza por nivel de evidencia
│              │    Selecciona top-5
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Context     │  → Construye el contexto para el LLM
│  Builder     │    Incluye: chunks + metadata + historial
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  LLM         │  → Genera respuesta con system prompt
│  (Claude)    │    Incluye citación de fuentes
│              │    Respeta nivel de evidencia
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Response    │  → Formatea respuesta + fuentes
│  Formatter   │    Agrega metadata (tokens, tiempo)
└──────────────┘
```

## 4. System Prompt del Agente

```python
SYSTEM_PROMPT = """
Sos KineIA, un asistente EXPERTO en kinesiología y fisioterapia.

## Tu rol:
- Respondés consultas de estudiantes y profesionales de kinesiología en Argentina
- Basás tus respuestas EXCLUSIVAMENTE en las fuentes proporcionadas en el contexto
- SIEMPRE citás las fuentes al final de tu respuesta
- Si no encontrás información en el contexto, decís "No tengo información verificada sobre ese tema"
- NUNCA inventás información médica o protocolos

## Niveles de evidencia:
- 🟢 Protocolo oficial / Guía clínica del gobierno → Máxima confiabilidad
- 🔵 Libro de referencia universitario → Alta confiabilidad
- 🟡 Paper / Investigación publicada → Confiabilidad moderada
- 🟠 Apunte universitario → Referencia complementaria

## Formato de respuesta:
1. Respuesta clara y directa
2. Si aplica, estructura con subtítulos
3. Al final, sección "📚 Fuentes" con las referencias

## Modos:
- Estudiante: Explicaciones didácticas, ejemplos, referencias a exámenes
- Profesional: Respuestas técnicas, protocolos, evidencia clínica
- Examen: Genera preguntas de práctica con explicaciones

## Contexto: {context}
## Historial: {history}
"""
```

## 5. Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://kineia:${DB_PASSWORD}@postgres:5432/kineia
      - QDRANT_URL=http://qdrant:6333
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - qdrant
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=kineia
      - POSTGRES_USER=kineia
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certbot:/etc/letsencrypt
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
```

## 6. Decisiones de Diseño

### D1: Qdrant vs Chroma vs Pinecone
**Elegido: Qdrant**
- Open-source, self-hosted (sin costos de API)
- Filtros avanzados nativos (perfecto para filtrar por área/tipo)
- Rendimiento superior en producción
- Docker-ready

### D2: Claude vs GPT vs Ollama
**Elegido: Claude (primario) + Ollama (fallback)**
- Claude 3.5 Sonnet: mejor razonamiento en español
- Ollama como fallback local si la API falla
- Arquitectura permite cambiar LLM fácilmente

### D3: FastAPI vs Django vs Express
**Elegido: FastAPI**
- Async nativo (importante para RAG pipeline)
- Tipado con Pydantic
- OpenAPI automático
- Ecosistema ML/AI maduro en Python

### D4: Next.js vs Astro vs SvelteKit
**Elegido: Next.js 15**
- SSR para SEO
- React 19 con Server Components
- Ecosystem maduro
- Streaming responses (para chat en tiempo real)

### D5: Embeddings Model
**Elegido: all-MiniLM-L6-v2**
- Gratuito y local
- 384 dimensiones (eficiente)
- Buen rendimiento en múltiples idiomas
- Fallback: text-embedding-3-small (OpenAI) si necesitamos más calidad
