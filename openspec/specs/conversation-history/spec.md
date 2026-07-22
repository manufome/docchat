# Historial de Conversaciones

## Propósito

Crear, listar, recuperar y eliminar conversaciones con sus mensajes asociados.

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| CONV-01 | El sistema DEBE crear una conversación con título opcional | MUST |
| CONV-02 | El sistema DEBE listar las conversaciones del usuario ordenadas por actualización descendente | MUST |
| CONV-03 | El sistema DEBE recuperar los mensajes de una conversación | MUST |
| CONV-04 | El sistema DEBE eliminar una conversación y sus mensajes asociados | MUST |
| CONV-05 | El sistema DEBE retornar 404 al acceder o eliminar una conversación inexistente o de otro usuario | MUST |

### CONV-01: Creación de conversación

- GIVEN un usuario autenticado
- WHEN se envía POST /api/conversations sin título o con título opcional
- THEN el sistema crea la conversación y retorna 201 con los datos de la conversación

### CONV-02: Listado de conversaciones

- GIVEN un usuario autenticado con 5 conversaciones
- WHEN se envía GET /api/conversations
- THEN el sistema retorna 200 con las conversaciones ordenadas por updated_at descendente

### CONV-03: Recuperación de mensajes

- GIVEN un usuario autenticado con una conversación que contiene mensajes
- WHEN se envía GET /api/conversations/{id}/messages
- THEN el sistema retorna 200 con los mensajes ordenados cronológicamente, incluyendo role, contenido y citas

### CONV-04: Eliminación de conversación

- GIVEN un usuario autenticado con una conversación existente
- WHEN se envía DELETE /api/conversations/{id}
- THEN el sistema elimina la conversación y todos sus mensajes, y retorna 200

### CONV-05: Acceso a conversación inexistente

- GIVEN un usuario autenticado
- WHEN se envía GET /api/conversations/{id}/messages con un ID de conversación inexistente
- THEN el sistema retorna 404
