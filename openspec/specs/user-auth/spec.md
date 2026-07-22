# Autenticación de Usuario

## Propósito

Gestionar el registro, inicio de sesión y acceso autenticado mediante tokens JWT.

## Requerimientos

| ID | Descripción | Fuerza |
|----|-------------|--------|
| AUTH-01 | El sistema DEBE rechazar registros con email duplicado | MUST |
| AUTH-02 | El sistema DEBE validar formato de email | MUST |
| AUTH-03 | El sistema DEBE exigir contraseña de al menos 8 caracteres | MUST |
| AUTH-04 | El sistema DEBE devolver un JWT en registro e inicio de sesión exitosos | MUST |
| AUTH-05 | El sistema DEBE rechazar credenciales inválidas con error 401 | MUST |
| AUTH-06 | El sistema DEBE exponer el perfil del usuario autenticado vía GET /me | MUST |

### AUTH-01: Registro exitoso

- GIVEN un email y contraseña válidos
- WHEN se envía POST /api/auth/register
- THEN el sistema crea el usuario, hashea la contraseña y retorna 201 con JWT + datos del usuario

### AUTH-02: Registro con email duplicado

- GIVEN un email ya registrado
- WHEN se envía POST /api/auth/register con el mismo email
- THEN el sistema retorna 409 y no crea el usuario

### AUTH-03: Inicio de sesión exitoso

- GIVEN un usuario registrado con credenciales correctas
- WHEN se envía POST /api/auth/login
- THEN el sistema retorna 200 con JWT + datos del usuario

### AUTH-04: Inicio de sesión con contraseña incorrecta

- GIVEN un usuario registrado
- WHEN se envía POST /api/auth/login con contraseña incorrecta
- THEN el sistema retorna 401

### AUTH-05: Perfil autenticado

- GIVEN un JWT válido en el encabezado Authorization
- WHEN se envía GET /api/auth/me
- THEN el sistema retorna 200 con los datos del usuario

### AUTH-06: Perfil sin token

- GIVEN una solicitud sin encabezado Authorization
- WHEN se envía GET /api/auth/me
- THEN el sistema retorna 401
