# Propuesta: DocChat

## Intención

Obtener respuestas precisas de documentos (PDF, DOCX, XLSX) mediante lenguaje natural, sin leer archivos completos ni exponer datos a terceros.

## Alcance

### Dentro del alcance
- Registro e inicio de sesión (JWT)
- Configuración de clave API de OpenAI por usuario
- Carga de documentos por arrastrar y soltar (PDF, DOCX, XLSX; máx. 4 archivos, 10 MB c/u)
- Listado y eliminación de documentos
- Conversaciones con respuestas en flujo continuo (SSE)
- Citas textuales con referencia a páginas
- Respuesta "No lo sé" cuando no hay respuesta en los documentos
- Historial de conversaciones

### Fuera del alcance
- Panel de administración, vista previa de documentos, uso compartido
- Carga masiva, actualización de documentos (solo eliminar y recargar)
- Monitoreo, analíticas, aplicación móvil
- Frameworks de orquestación como LangChain

## Capacidades

### Capacidades nuevas
- `user-auth`: registro, inicio de sesión y renovación de JWT
- `user-profile`: gestión de clave API de OpenAI
- `file-upload`: carga, validación y almacenamiento
- `document-management`: listado y eliminación de documentos
- `rag-chat`: conversación con respuestas en flujo y citas
- `conversation-history`: persistencia y recuperación del historial

### Capacidades modificadas
Ninguna.

## Enfoque

Monorepo con `backend/` (Python FastAPI) y `frontend/` (React + TypeScript + Vite + Tailwind). La lógica RAG en `backend/rag/` está aislada de HTTP. El flujo embebe la pregunta, recupera contexto de ChromaDB con filtro por usuario, construye una indicación y transmite la respuesta desde OpenAI mediante SSE.

## Áreas afectadas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `backend/` | Nuevo | API REST, servicios, lógica RAG, modelos |
| `frontend/` | Nuevo | Interfaz de usuario completa |
| `openspec/specs/` | Nuevo | Especificaciones de cada capacidad |

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Calidad del fragmentado | Media | Ajustar tamaño y solapamiento |
| Fiabilidad de citas | Media | Validar con pruebas; refinar indicación |
| Inyección de instrucciones | Baja | Defensas en la indicación del sistema |

## Plan de reversión

Restaurar base de datos y ChromaDB desde respaldos; volver al commit previo.

## Dependencias

- Python 3.11+, Node.js 20+
- OpenAI API (clave del usuario)
- PyMuPDF, python-docx, openpyxl
- sentence-transformers (all-MiniLM-L6-v2)
- ChromaDB

## Criterios de éxito

- [ ] Un usuario se registra y configura su clave API
- [ ] Carga un PDF: el sistema lo fragmenta, embebe y almacena
- [ ] Pregunta y recibe respuesta con citas a páginas correctas
- [ ] Responde "No lo sé" cuando la respuesta no está en los documentos
- [ ] La conversación persiste al recargar la página
- [ ] Se respeta el límite de 4 archivos por usuario
