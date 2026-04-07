# KineIA - Especificaciones Técnicas

## 1. Requisitos Funcionales

### RF-01: Chat Conversacional
- El usuario puede hacer preguntas en español sobre kinesiología
- El agente responde con información verificada y citación de fuentes
- Soporte para conversaciones multi-turno (contexto)
- Historial de conversaciones persistente

### RF-02: Búsqueda Semántica (RAG)
- Búsqueda vectorial sobre la base de conocimiento
- Filtrado por área (neurología, deporte, respiratorio, etc.)
- Filtrado por tipo de fuente (libro, protocolo, paper, apunte)
- Filtrado por universidad (UNC, UBA, etc.)
- Ranking por relevancia semántica + nivel de evidencia

### RF-03: Citación de Fuentes
- Cada respuesta incluye fuentes consultadas
- Formato: [Autor, Libro/Paper, Año, Página/Capítulo]
- Diferenciación visual entre niveles de evidencia:
  - 🟢 Protocolo oficial / Guía clínica
  - 🔵 Libro de referencia
  - 🟡 Paper / Investigación
  - 🟠 Apunte universitario
  - ⚪ Conocimiento general del modelo

### RF-04: Modos de Uso
- **Modo Estudiante**: Enfocado en materias, exámenes, bibliografía
- **Modo Profesional**: Enfocado en protocolos, guías clínicas, evidencia
- **Modo Examen**: Preguntas de práctica con respuestas explicadas

### RF-05: Ingesta de Documentos
- Pipeline para procesar PDFs, Markdown, texto plano
- Chunking inteligente respetando estructura del documento
- Extracción automática de metadata
- Actualización incremental de la base vectorial

### RF-06: Panel de Administración
- Dashboard con métricas de uso
- Gestión de documentos (agregar, eliminar, actualizar)
- Visualización de fuentes indexadas
- Logs de consultas

## 2. Requisitos No Funcionales

### RNF-01: Performance
- Tiempo de respuesta: < 5 segundos para consultas simples
- Tiempo de respuesta: < 10 segundos para consultas complejas
- Soporte para 50 usuarios concurrentes (v1)

### RNF-02: Disponibilidad
- Uptime 99% (VPS)
- Recuperación automática ante fallos
- Health checks cada 60 segundos

### RNF-03: Seguridad
- HTTPS obligatorio
- Autenticación de usuarios (registro/login)
- Rate limiting (100 consultas/hora por usuario)
- Sanitización de inputs

### RNF-04: Escalabilidad
- Arquitectura modular (microservicios)
- Vector DB separada del backend
- LLM intercambiable (Claude / GPT / Ollama)

### RNF-05: Datos
- Backup diario de la base vectorial
- Backup diario de PostgreSQL
- Logs estructurados (JSON)

## 3. API Specification

### Endpoints

```
POST   /api/v1/chat              # Enviar mensaje al agente
GET    /api/v1/chat/history       # Obtener historial
DELETE /api/v1/chat/history/{id}  # Eliminar conversación

GET    /api/v1/search             # Búsqueda semántica directa
GET    /api/v1/search/filters     # Obtener filtros disponibles

POST   /api/v1/auth/register      # Registro
POST   /api/v1/auth/login         # Login
POST   /api/v1/auth/refresh       # Refresh token

GET    /api/v1/knowledge/stats    # Estadísticas de la base
POST   /api/v1/knowledge/ingest   # Ingestar documento (admin)
DELETE /api/v1/knowledge/{id}     # Eliminar documento (admin)

GET    /api/v1/health             # Health check
```

### Chat Request/Response

```json
// Request
POST /api/v1/chat
{
  "message": "¿Cuáles son las fases de rehabilitación post ACV?",
  "mode": "profesional",
  "conversation_id": "uuid-optional",
  "filters": {
    "areas": ["neurologia"],
    "source_types": ["protocolo", "libro"]
  }
}

// Response
{
  "id": "msg-uuid",
  "conversation_id": "conv-uuid",
  "response": "La rehabilitación post ACV se divide en 3 fases principales...",
  "sources": [
    {
      "title": "Consenso de ACV Isquémico Agudo",
      "type": "protocolo",
      "evidence_level": "green",
      "year": 2019,
      "publisher": "Revista Medicina Buenos Aires",
      "relevance_score": 0.95
    },
    {
      "title": "Umphred's Neurological Rehabilitation",
      "type": "libro",
      "evidence_level": "blue",
      "year": 2019,
      "publisher": "Elsevier",
      "relevance_score": 0.87
    }
  ],
  "mode": "profesional",
  "tokens_used": 1250,
  "response_time_ms": 3200
}
```

## 4. Escenarios de Uso

### Escenario 1: Estudiante preparando examen de Anatomía (UNC)
```
Usuario: "¿Cuáles son los movimientos de la articulación del hombro según Kapandji?"
Agente: [Busca en libros/anatomia/kapandji] → Responde con los movimientos
        + cita Kapandji Tomo I + sugiere ejercicios de práctica
```

### Escenario 2: Profesional buscando protocolo de lesión medular
```
Usuario: "¿Cuál es el protocolo de rehabilitación para lesión medular completa?"
Agente: [Busca en protocolos/lesion-medular-inareps] → Responde con el protocolo
        + cita INAREPs 2018 + diferencia por nivel de lesión
```

### Escenario 3: Kinesiólogo en UCI buscando protocolo de extubación
```
Usuario: "Protocolo de destete de ventilación mecánica"
Agente: [Busca en protocolos/vm + guias/respiratorio] → Responde con pasos
        + cita SATI + criterios de destete
```

### Escenario 4: Modo examen
```
Usuario: "Pregúntame sobre biomecánica de rodilla"
Agente: [Genera pregunta basada en banco de preguntas UNC]
        "¿Cuáles son los ejes de movimiento de la rodilla?"
        + espera respuesta + evalúa + explica
```

## 5. Modelo de Datos

### Tablas PostgreSQL

```sql
-- Usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'student', -- student, professional, admin
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversaciones
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    mode VARCHAR(50), -- estudiante, profesional, examen
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Mensajes
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20), -- user, assistant
    content TEXT NOT NULL,
    sources JSONB,
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documentos indexados
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source_type VARCHAR(50), -- libro, protocolo, paper, apunte
    area VARCHAR(100), -- neurologia, respiratorio, etc.
    university VARCHAR(100),
    materia VARCHAR(200),
    author VARCHAR(500),
    year INTEGER,
    publisher VARCHAR(255),
    evidence_level VARCHAR(20), -- green, blue, yellow, orange
    chunk_count INTEGER,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Colección Qdrant

```json
{
  "collection": "kineia_knowledge",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  },
  "payload_schema": {
    "document_id": "uuid",
    "chunk_index": "integer",
    "text": "text",
    "source_type": "keyword",
    "area": "keyword",
    "university": "keyword",
    "materia": "keyword",
    "evidence_level": "keyword",
    "year": "integer"
  }
}
```
