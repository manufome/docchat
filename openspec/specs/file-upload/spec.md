# Carga de Archivos

## Propósito

Aceptar, validar y procesar documentos del usuario para su uso en el chat RAG.

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| UPLD-01 | El sistema DEBE aceptar archivos PDF, DOCX y XLSX | MUST |
| UPLD-02 | El sistema DEBE rechazar archivos mayores a 10 MB | MUST |
| UPLD-03 | El sistema DEBE limitar a 4 archivos por usuario | MUST |
| UPLD-04 | El sistema DEBE validar el tipo de archivo por extensión y MIME | MUST |
| UPLD-05 | El sistema DEBE iniciar el procesamiento tras la carga exitosa | MUST |
| UPLD-06 | El sistema DEBE marcar el documento como "processing" durante el proceso | MUST |

### UPLD-01: Carga exitosa de PDF

- GIVEN un usuario autenticado con menos de 4 documentos
- WHEN se envía POST /api/documents/upload con un PDF válido menor a 10 MB
- THEN el sistema acepta el archivo, inicia el procesamiento y retorna 201 con estado "processing"

### UPLD-02: Archivo excede tamaño máximo

- GIVEN un usuario autenticado
- WHEN se envía POST /api/documents/upload con un archivo mayor a 10 MB
- THEN el sistema retorna 413 y no guarda el archivo

### UPLD-03: Límite de archivos alcanzado

- GIVEN un usuario autenticado con 4 documentos existentes
- WHEN se envía POST /api/documents/upload con un archivo válido
- THEN el sistema retorna 409 y no acepta el archivo

### UPLD-04: Tipo de archivo no soportado

- GIVEN un usuario autenticado
- WHEN se envía POST /api/documents/upload con un archivo .txt o .png
- THEN el sistema retorna 400 y no acepta el archivo

### UPLD-05: Procesamiento completo

- GIVEN un archivo cargado exitosamente con estado "processing"
- WHEN el pipeline de fragmentación, embebido y almacenamiento en ChromaDB finaliza sin errores
- THEN el sistema actualiza el estado del documento a "ready"
