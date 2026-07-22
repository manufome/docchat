# Diseño Técnico: DocChat

## Enfoque Técnico

Monorepo con `backend/` (Python FastAPI) y `frontend/` (React + TypeScript + Vite + Tailwind). La lógica RAG en `backend/rag/` permanece aislada de HTTP. El flujo principal: el usuario carga documentos → se fragmentan en trozos de 512 tokens → se embeben con all-MiniLM-L6-v2 → se almacenan en ChromaDB con filtro por `user_id`. Al consultar: se embebe la pregunta → se recuperan los 5 trozos más relevantes → se construye una indicación con contexto → se transmite la respuesta desde GPT-4o mediante SSE.

## Decisiones de Arquitectura

| Decisión | Opciones | Elección | Justificación |
|---|---|---|---|
| Capa RAG aislada | Capa única vs separada | `rag/` independiente | Sin acoplamiento HTTP: testeable y reutilizable |
| Colección ChromaDB | Una por usuario vs única con filtro | Única + metadato `user_id` | Menos sobrecarga administrativa; ChromaDB filtra en consulta |
| Embeddings locales | API externa vs local | sentence-transformers local | Sin costos recurrentes; 384 dimensiones suficiente; carga única al iniciar |
| Streaming | WebSocket vs SSE | SSE (eventos del servidor) | Más simple; compatible con `fetch` + `ReadableStream` |
| Clave Fernet | Variable aparte vs derivada | Derivada de `SECRET_KEY` vía SHA-256 | Sin变量 adicional; misma seguridad |
| Fragmentación | Varios tamaños | 512 tokens, 128 solapamiento | Equilibrio entre granularidad y contexto |

## Flujo de Datos

### Carga de documento

```
Usuario → FileDropzone → POST /api/documents/upload (multipart)
  → Backend: valida tipo/tamaño/límite
  → Crea Document (estado: processing)
  → Guarda archivo en disco (uploads/{user_id}/{doc_id}/)
  → Fragmenta (chunking.py)
  → Embebe cada trozo (embedding.py)
  → Almacena en ChromaDB con metadatos: user_id, doc_id, pagina
  → Actualiza Document (estado: ready)
  → Responde 201
```

### Chat con streaming

```
Usuario → ChatInput → POST /api/chat/stream (JSON)
  → chat_service:
    → Guarda mensaje del usuario en DB
    → Embebe la consulta (embedding.py)
    → Recupera top-5 de ChromaDB (filtro: user_id)
    → Construye indicación RAG (prompt.py)
    → Inicia StreamingResponse con GPT-4o
    → Emite SSE: event:token → event:citation → event:done
    → Guarda respuesta completa en DB
  → Frontend: useChat hook lee ReadableStream
    → Acumula tokens en MessageBubble
    → Muestra citas en CitationPopover
```

## Modelo de Datos

### SQLAlchemy (SQLite/PostgreSQL)

| Tabla | Columnas clave | Índices |
|---|---|---|
| `User` | id (PK), email (único), hashed_password, encrypted_api_key, created_at | unique(email) |
| `Document` | id (PK), user_id (FK), filename, file_type, file_size, status, file_path, created_at | idx(user_id) |
| `Conversation` | id (PK), user_id (FK), title, created_at, updated_at | idx(user_id), idx(updated_at) |
| `Message` | id (PK), conversation_id (FK), role, content, citations (JSON), created_at | idx(conversation_id) |

### ChromaDB

Colección `"documents"` — vector 384-dim float32 — distancia coseno — metadatos: `{user_id, doc_id, chunk_index, pagina, texto}`

## Cambios de Archivos

| Archivo | Acción | Descripción |
|---|---|---|
| `backend/app/main.py` | Crear | App FastAPI: lifespan, CORS, montaje de rutas |
| `backend/app/core/config.py` | Crear | Configuración con Pydantic Settings + variables de entorno |
| `backend/app/core/security.py` | Crear | JWT, bcrypt, Fernet |
| `backend/app/core/deps.py` | Crear | Inyección de dependencias: get_db, get_current_user, get_embedder |
| `backend/app/api/auth.py` | Crear | POST /register, POST /login, GET /me |
| `backend/app/api/users.py` | Crear | PUT /users/me/api-key |
| `backend/app/api/documents.py` | Crear | POST /upload, GET /, DELETE /{id} |
| `backend/app/api/conversations.py` | Crear | CRUD de conversaciones y mensajes |
| `backend/app/api/chat.py` | Crear | POST /chat/stream con SSE |
| `backend/app/models/*.py` | Crear | Modelos SQLAlchemy (4 tablas) |
| `backend/app/schemas/*.py` | Crear | Esquemas Pydantic para validación |
| `backend/app/services/*.py` | Crear | Orquestación: auth, documento, chat, conversación |
| `backend/app/rag/*.py` | Crear | fragmentacion.py, embebido.py, recuperacion.py, indicacion.py |
| `backend/app/db/*.py` | Crear | Motor asíncrono SQLAlchemy + base declarativa |
| `backend/tests/*.py` | Crear | Pruebas unitarias y de integración |
| `frontend/src/**` | Crear | Componentes, páginas, hooks, tipos, contextos |

## Detalles de Implementación Clave

**Carga del modelo de embeddings**: Se carga una vez en el ciclo de vida de FastAPI (`lifespan`) y se guarda en `app.state.embedder`. SentenceTransformer se obtiene con nombre del modelo desde configuración.

**Inicialización de ChromaDB**: `chromadb.PersistentClient(path=CHROMA_PATH)` también en el ciclo de vida. Se obtiene o crea la colección `"documents"`.

**Derivación de clave Fernet**: `base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())` — 32 bytes, sin variable de entorno adicional.

**Manejo de errores en SSE**: Si OpenAI falla durante la transmisión, se captura la excepción y se emite `event: error\ndata: {"detail": "<mensaje>"}\n\n`. El frontend detecta el evento, detiene la acumulación y muestra el error.

**Limpieza de archivos**: Al eliminar un documento, se borra el archivo del disco y los fragmentos de ChromaDB con `coleccion.delete(where={"doc_id": <id>})`.

## Estrategia de Pruebas

| Capa | Qué probar | Enfoque |
|---|---|---|
| Unitaria | `fragmentacion.py`, `indicacion.py` | Datos sintéticos, aserciones directas |
| Integración | `embebido.py`, `recuperacion.py` | ChromaDB efímera; simular SentenceTransformer con vectores fijos |
| API | Todos los puntos de acceso | `httpx.AsyncClient` + `TestClient`; simular OpenAI y ChromaDB |
| SSE | `POST /chat/stream` | Leer `StreamingResponse` con respuestas predecibles |
| Frontend | Componentes, hooks | Vitest + `testing-library`; simular `fetch` |

### Simulaciones (mocks)

- **sentence-transformers**: función que devuelve vectores fijos de 384 dimensiones
- **OpenAI**: `MagicMock` que itera fragmentos de texto conocidos con citas
- **ChromaDB**: `chromadb.Client(Settings(anonymized_telemetry=False))` en modo efímero

## Matriz de Amenazas

N/A — El diseño no involucra enrutamiento de red, comandos de terminal, subprocesos, automatización de VCS/PR, clasificación de archivos ejecutables ni integración con procesos externos.

## Migración / Despliegue

Sin migración inicial. `Base.metadata.create_all()` en el ciclo de vida para desarrollo. Producción usará Alembine.

## Preguntas Abiertas

- [ ] ¿Ubicación de almacenamiento de archivos en producción? Disco local vs S3
- [ ] ¿Límite de tokens máximos por respuesta de OpenAI? Definir `max_tokens`
- [ ] ¿Tiempo de espera máximo para la respuesta de OpenAI?
