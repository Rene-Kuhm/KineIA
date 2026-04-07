# KineIA - Task Breakdown

## Fase 1: Infraestructura + Base de Conocimiento

### T1.1: Setup del proyecto
- [ ] Inicializar backend (FastAPI + pyproject.toml)
- [ ] Inicializar frontend (Next.js 15)
- [ ] Crear docker-compose.yml con todos los servicios
- [ ] Crear .env.example
- [ ] Configurar PostgreSQL + migraciones
- [ ] Configurar Qdrant
- [ ] Configurar CI básico

### T1.2: Base de conocimiento - Estructura
- [ ] Crear estructura de directorios knowledge_base/
- [ ] Crear documentos Markdown para cada universidad (UNC, UBA, UNSL, Favaloro)
- [ ] Crear documentos para cada materia de UNC (25 asignaturas)
- [ ] Crear documentos para libros de referencia (25+ títulos)
- [ ] Crear documentos para protocolos clínicos oficiales
- [ ] Crear documentos para guías clínicas por especialidad
- [ ] Crear documentos para papers de investigación

### T1.3: Pipeline de ingesta
- [ ] Implementar extractor de Markdown
- [ ] Implementar extractor de PDF
- [ ] Implementar extractor de texto plano
- [ ] Implementar chunker inteligente (512 tokens, overlap 50)
- [ ] Implementar extractor de metadata
- [ ] Implementar clasificador de nivel de evidencia
- [ ] Implementar embedder (sentence-transformers)
- [ ] Implementar upsert a Qdrant
- [ ] Crear script seed-knowledge.py

---

## Fase 2: RAG Pipeline + Chat

### T2.1: RAG Pipeline
- [ ] Implementar query analyzer (detectar área, intent)
- [ ] Implementar retriever (búsqueda vectorial en Qdrant)
- [ ] Implementar filtros (área, tipo, universidad)
- [ ] Implementar reranker (re-ranking por relevancia + evidencia)
- [ ] Implementar context builder
- [ ] Implementar response formatter (con citación)

### T2.2: LLM Integration
- [ ] Implementar provider Claude (Anthropic SDK)
- [ ] Implementar provider Ollama (fallback local)
- [ ] Crear system prompt del agente
- [ ] Implementar LangChain chains
- [ ] Implementar streaming de respuestas

### T2.3: Chat API
- [ ] Implementar POST /api/v1/chat
- [ ] Implementar GET /api/v1/chat/history
- [ ] Implementar DELETE /api/v1/chat/history/{id}
- [ ] Implementar manejo de conversaciones multi-turno
- [ ] Implementar modos (estudiante, profesional, examen)

### T2.4: Search API
- [ ] Implementar GET /api/v1/search
- [ ] Implementar GET /api/v1/search/filters
- [ ] Implementar búsqueda con filtros combinados

---

## Fase 3: Frontend

### T3.1: Setup Frontend
- [ ] Configurar Next.js 15 con App Router
- [ ] Configurar Tailwind CSS 4
- [ ] Configurar API client
- [ ] Crear layout principal

### T3.2: Chat UI
- [ ] Implementar ChatWindow component
- [ ] Implementar MessageBubble (user + assistant)
- [ ] Implementar SourceCard (citación de fuentes)
- [ ] Implementar ModeSelector (estudiante/profesional/examen)
- [ ] Implementar streaming de respuestas
- [ ] Implementar historial de conversaciones

### T3.3: Dashboard
- [ ] Implementar landing page
- [ ] Implementar registro/login
- [ ] Implementar dashboard de usuario
- [ ] Implementar panel de administración

---

## Fase 4: Deploy + Testing

### T4.1: Auth
- [ ] Implementar registro de usuarios
- [ ] Implementar login (JWT)
- [ ] Implementar rate limiting
- [ ] Implementar roles (student, professional, admin)

### T4.2: Testing
- [ ] Tests unitarios del RAG pipeline
- [ ] Tests de integración del chat
- [ ] Tests del pipeline de ingesta
- [ ] Test con preguntas de exámenes reales de UNC
- [ ] Benchmark de calidad de respuestas

### T4.3: Deploy en VPS
- [ ] Configurar Docker en VPS
- [ ] Deploy con docker-compose
- [ ] Configurar Nginx como reverse proxy
- [ ] Configurar SSL (Let's Encrypt)
- [ ] Configurar backups automáticos
- [ ] Configurar monitoreo (health checks)

---

## Prioridad de Implementación

| Prioridad | Tarea | Descripción |
|-----------|-------|-------------|
| 🔴 P0 | T1.1 | Setup del proyecto |
| 🔴 P0 | T1.2 | Base de conocimiento |
| 🔴 P0 | T1.3 | Pipeline de ingesta |
| 🟠 P1 | T2.1 | RAG Pipeline |
| 🟠 P1 | T2.2 | LLM Integration |
| 🟠 P1 | T2.3 | Chat API |
| 🟡 P2 | T3.1 | Setup Frontend |
| 🟡 P2 | T3.2 | Chat UI |
| 🟢 P3 | T2.4 | Search API |
| 🟢 P3 | T3.3 | Dashboard |
| 🟢 P3 | T4.1 | Auth |
| 🔵 P4 | T4.2 | Testing |
| 🔵 P4 | T4.3 | Deploy |

## Dependencias

```
T1.1 → T1.2 → T1.3 → T2.1 → T2.2 → T2.3
                                       ↓
                               T3.1 → T3.2
                                       ↓
                               T4.1 → T4.2 → T4.3
```
