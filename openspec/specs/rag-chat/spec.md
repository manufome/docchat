# Chat RAG

## Propósito

Responder preguntas del usuario basándose exclusivamente en el contenido de sus documentos, mediante recuperación aumentada por generación (RAG) con transmisión en flujo continuo (SSE).

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| RAG-01 | El sistema DEBE recuperar fragmentos relevantes de ChromaDB filtrando por usuario | MUST |
| RAG-02 | El sistema DEBE construir una indicación RAG que limite la respuesta al contexto proporcionado | MUST |
| RAG-03 | El sistema DEBE transmitir la respuesta de GPT-4o mediante SSE con eventos token, citation y done | MUST |
| RAG-04 | El sistema DEBE responder "No lo sé" cuando el contexto no contenga información relevante | MUST |
| RAG-05 | El sistema DEBE incluir citas textuales con referencia al documento fuente | MUST |
| RAG-06 | El sistema DEBE guardar el mensaje del usuario y la respuesta del asistente en la base de datos | MUST |

### RAG-01: Pregunta con respuesta en documentos

- GIVEN un usuario autenticado con documentos procesados y una conversación existente
- WHEN se envía POST /api/chat/stream con conversation_id y un mensaje sobre el contenido de sus documentos
- THEN el sistema embebe la pregunta, recupera hasta 5 fragmentos de ChromaDB, construye la indicación, transmite tokens SSE con la respuesta y citas, y finaliza con done

### RAG-02: Pregunta sin respuesta en documentos

- GIVEN un usuario con documentos procesados
- WHEN se envía una pregunta fuera del alcance de sus documentos
- THEN el sistema responde "No lo sé" o equivalente, sin inventar información

### RAG-03: Eventos SSE

- GIVEN una solicitud de chat válida
- WHEN el sistema comienza a transmitir
- THEN cada fragmento de texto se emite como evento "token", cada cita como "citation", y al finalizar se emite "done"

### RAG-04: Usuario sin documentos

- GIVEN un usuario autenticado sin documentos cargados
- WHEN se envía POST /api/chat/stream
- THEN el sistema retorna un error indicando que no hay documentos disponibles para consultar
