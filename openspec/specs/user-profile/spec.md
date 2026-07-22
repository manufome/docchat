# Perfil de Usuario

## Propósito

Administrar la clave API de OpenAI asociada a cada cuenta.

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| PROF-01 | El sistema DEBE permitir al usuario autenticado actualizar su clave API de OpenAI | MUST |
| PROF-02 | El sistema DEBE verificar la clave API con una llamada de prueba a OpenAI antes de guardarla | MUST |
| PROF-03 | El sistema DEBE cifrar la clave API en reposo usando Fernet | MUST |
| PROF-04 | El sistema DEBE rechazar claves API inválidas o que no respondan | MUST |

### PROF-01: Actualización exitosa de clave API

- GIVEN un usuario autenticado con un JWT válido
- WHEN se envía PUT /api/users/me/api-key con una clave API de OpenAI válida
- THEN el sistema verifica la clave con una llamada de prueba, la cifra y la guarda, y retorna 200

### PROF-02: Clave API inválida

- GIVEN un usuario autenticado
- WHEN se envía PUT /api/users/me/api-key con una clave API inválida o revocada
- THEN el sistema retorna 400 sin guardar la clave

### PROF-03: Clave API sin autenticación

- GIVEN una solicitud sin JWT
- WHEN se envía PUT /api/users/me/api-key
- THEN el sistema retorna 401
