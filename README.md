# DocChat

Aplicación RAG (Generación Aumentada por Recuperación) para chatear con tus documentos. Subí PDFs, archivos de Word o Excel, y hace preguntas en lenguaje natural. La IA responde **exclusivamente** con el contenido de tus documentos y muestra la fuente exacta de cada respuesta.

**Demo:** [próximamente](#)
**Backend:** Python FastAPI | **Frontend:** React + TypeScript + Tailwind CSS

## Capturas

| Dashboard | Chat |
|-----------|------|
| *(pendiente)* | *(pendiente)* |

## Funcionalidades

- **Autenticación JWT** — registro e inicio de sesión
- **Subida de documentos** — arrastrar y soltar PDF, DOCX, XLSX (máx. 4 archivos, 10 MB cada uno)
- **Procesamiento automático** — al subir, el documento se parsea, fragmenta y convierte a vectores
- **Chat con flujo continuo** — las respuestas aparecen token por token vía SSE
- **Citas con fuente** — cada respuesta indica el documento y número de página donde encontró la información
- **Historial de conversaciones** — las conversaciones quedan guardadas para retomarlas después
- **Clave API propia** — cada usuario usa su propia clave de OpenAI, almacenada encriptada

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| Backend | Python FastAPI + SQLAlchemy async + Alembic |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Vector DB | ChromaDB (persistente, colección única con filtro por usuario) |
| Embeddings | sentence-transformers / all-MiniLM-L6-v2 |
| LLM | OpenAI GPT-4o (clave del usuario) |
| Autenticación | JWT + bcrypt + Fernet |
| Formato de respuestas | react-markdown + remark-gfm |
| Contenedores | Docker + docker-compose |

## Arquitectura

```
dochatapp/
├── backend/
│   ├── app/
│   │   ├── api/          # Rutas HTTP
│   │   ├── core/         # Configuración, seguridad, dependencias
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Esquemas Pydantic
│   │   ├── services/     # Orquestación (HTTP → RAG → DB)
│   │   ├── rag/          # Lógica RAG pura (sin HTTP ni BD)
│   │   └── db/           # Conexión a base de datos
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/   # Componentes React
│   │   ├── hooks/        # Hooks personalizados (useChat, useAuth...)
│   │   ├── pages/        # Páginas (Login, Dashboard, Chat, Settings)
│   │   ├── contexts/     # AuthContext, ToastProvider
│   │   └── lib/          # Cliente API, utilidades SSE
│   └── __tests__/
└── docker-compose.yml
```

La capa `rag/` está aislada del HTTP y la base de datos. Esto permite testear la lógica RAG sin levantar FastAPI, y cambiar ChromaDB por otro motor vectorial sin tocar ni una línea de fragmentación o generación de prompts.

## Inicio Rápido

### Prerrequisitos
- Python 3.12+
- Node.js 18+
- Una clave API de OpenAI

### Desarrollo

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Editar SECRET_KEY y otras variables
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

La aplicación corre en `http://localhost:5173`. El backend en `http://localhost:8000`. Documentación Swagger en `http://localhost:8000/docs`.

### Docker

```bash
docker compose up --build
```

La aplicación corre en `http://localhost`.

## Variables de Entorno

### Backend (`.env`)

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta para JWT y Fernet | (requerida) |
| `DATABASE_URL` | URL de conexión a la BD | `sqlite+aiosqlite:///./data/docchat.db` |
| `CHROMA_PATH` | Ruta de almacenamiento de ChromaDB | `./data/chroma` |
| `UPLOAD_DIR` | Directorio de archivos subidos | `./data/uploads` |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `http://localhost:5173` |
| `OPENAI_MAX_TOKENS` | Máximo de tokens por respuesta | `2048` |
| `OPENAI_TIMEOUT_SECONDS` | Timeout para llamadas a OpenAI | `30` |

### Frontend

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `VITE_API_URL` | URL base del backend | `http://localhost:8000` |

## API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Registrar usuario |
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/auth/me` | Perfil del usuario actual |
| PUT | `/api/users/me/api-key` | Configurar clave API de OpenAI |
| POST | `/api/documents/upload` | Subir documento |
| GET | `/api/documents` | Listar documentos |
| DELETE | `/api/documents/{id}` | Eliminar documento |
| POST | `/api/conversations` | Crear conversación |
| GET | `/api/conversations` | Listar conversaciones |
| GET | `/api/conversations/{id}/messages` | Mensajes de una conversación |
| DELETE | `/api/conversations/{id}` | Eliminar conversación |
| POST | `/api/chat/stream` | Chat con flujo continuo (SSE) |
| GET | `/api/health` | Estado del servidor |

## Decisiones Técnicas

- **Fragmentación de 512 caracteres con 128 de solapamiento**: el tamaño del fragmento es el parámetro que más impacta en la calidad de un RAG. 512 caracteres capturan párrafos completos sin ser demasiado grandes.
- **Embeddings locales con sentence-transformers**: cero costo por documento indexado. OpenAI solo se usa para generar respuestas.
- **Colección única en ChromaDB**: una sola colección con filtro por `user_id` en los metadatos. Si fuera una colección por usuario, habría que gestionar el ciclo de vida, y ChromaDB no escala bien con miles de colecciones.
- **SSE con `fetch` + `ReadableStream`**: `EventSource` no soporta POST, y necesitamos POST para enviar el mensaje junto con el token JWT.
- **Capa RAG aislada**: la lógica de fragmentación, embedding y recuperación no sabe de HTTP ni de base de datos. Se puede testear sin levantar el servidor y se puede cambiar ChromaDB por Pinecone sin tocar el chunking.

## Pruebas

```bash
# Backend
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# Frontend
cd frontend
npx vitest run
```

**Cobertura actual:** 197 pruebas (135 backend + 62 frontend).

## Roadmap

- [x] Autenticación y perfiles de usuario
- [x] Subida y procesamiento de documentos
- [x] Chat con flujo continuo y citas
- [x] Historial de conversaciones
- [x] Docker
- [ ] Vista previa de documentos en el navegador
- [ ] Arrastrar múltiples archivos a la vez
- [ ] Búsqueda híbrida (vectorial + lexical)
- [ ] Compartir documentos entre usuarios
- [ ] Despliegue en producción

## Autor

**Manuel Forero** — Junior Web Developer

- GitHub: [@manufome](https://github.com/manufome)
- LinkedIn: [Manuel Forero](https://linkedin.com/in/manuel-forero)
