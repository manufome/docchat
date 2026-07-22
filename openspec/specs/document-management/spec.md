# Gestión de Documentos

## Propósito

Listar y eliminar documentos del usuario.

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| DOC-01 | El sistema DEBE listar los documentos del usuario autenticado | MUST |
| DOC-02 | El sistema DEBE eliminar un documento por ID incluyendo sus fragmentos en ChromaDB y archivo en disco | MUST |
| DOC-03 | El sistema DEBE retornar 404 al intentar acceder o eliminar un documento inexistente | MUST |
| DOC-04 | El sistema DEBE rechazar operaciones sobre documentos de otro usuario | MUST |

### DOC-01: Listado de documentos

- GIVEN un usuario autenticado con 3 documentos cargados
- WHEN se envía GET /api/documents
- THEN el sistema retorna 200 con un arreglo de 3 documentos con sus metadatos (id, nombre, tipo, estado, fecha)

### DOC-02: Listado vacío

- GIVEN un usuario autenticado sin documentos
- WHEN se envía GET /api/documents
- THEN el sistema retorna 200 con un arreglo vacío

### DOC-03: Eliminación exitosa

- GIVEN un usuario autenticado con un documento existente
- WHEN se envía DELETE /api/documents/{id}
- THEN el sistema elimina el registro, los fragmentos en ChromaDB y el archivo en disco, y retorna 200

### DOC-04: Eliminación de documento inexistente

- GIVEN un usuario autenticado
- WHEN se envía DELETE /api/documents/{id} con un ID que no existe
- THEN el sistema retorna 404

### DOC-05: Eliminación de documento ajeno

- GIVEN un usuario autenticado
- WHEN se envía DELETE /api/documents/{id} con el ID de un documento de otro usuario
- THEN el sistema retorna 404
