# Bitacora - Actividad 04: API REST segura (Flask)

Fecha: 2026-08-17
Carpeta de la actividad: `Seguridad/04/`

## 1. Endpoints definidos y su proposito

| Metodo | Ruta        | Proposito                                              | Autenticacion |
|--------|-------------|---------------------------------------------------------|---------------|
| GET    | `/health`   | Estado del servicio (liveness check).                   | Publico       |
| GET    | `/usuarios` | Lista de usuarios (id, nombre, email). Admite filtro `?id=` para devolver un unico usuario. | Requiere token Bearer |

Detalles de implementacion (`app.py`):
- `/usuarios` valida el parametro `id` con la expresion regular `^\d{1,10}$` antes de usarlo, devolviendo `400` si no cumple el formato y `404` si el id no existe.
- La respuesta de `/usuarios` solo expone los campos `id`, `nombre`, `email` (allow-list explicita, sin datos sensibles).
- CORS restringido al origen `https://app.mibanco.com` (configurable via `ALLOWED_ORIGIN`), solo metodo `GET`, sin credenciales (`supports_credentials=False`).
- Cabeceras de seguridad aplicadas a toda respuesta: `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`.
- `debug=False` en el arranque de Flask (evita exponer el depurador interactivo de Werkzeug).

## 2. Token de autenticacion (de prueba) y donde se guarda

- El token **no** esta hardcodeado en el codigo. Se lee desde la variable de entorno `API_TOKEN` (`app.py`, linea 23) y la app se niega a arrancar si no esta definida.
- Para las pruebas de esta actividad se genero un token de un solo uso con:
  ```
  python -c "import secrets;print(secrets.token_urlsafe(32))"
  ```
- El token de prueba se exporto solo en la sesion de shell local (`export API_TOKEN=...`) y **no se subio al repositorio**. No se persiste en ningun archivo versionado.
- La comparacion del token recibido contra `API_TOKEN` usa `secrets.compare_digest` (comparacion en tiempo constante) para mitigar ataques de timing.

## 3. Hallazgos del OWASP API Top 10 revisados con IA

Revision completa registrada en `evidencias/EVI-2026-08-17-04-revision-api.png`. Resumen:

- **API1 Broken Object Level Authorization**: OK. Token a nivel de servicio, sin datos por-usuario sensibles.
- **API2 Broken Authentication**: HALLAZGO — token estatico sin expiracion/rotacion y sin rate limiting en `/usuarios`, expuesto a fuerza bruta. Recomendacion: `flask-limiter` + rotacion periodica.
- **API3 Broken Object Property Level Authorization**: OK. Respuesta con allow-list de campos, sin sobre-exposicion de datos.
- **API4 Unrestricted Resource Consumption**: HALLAZGO — sin rate limiting ni paginacion en ningun endpoint. Riesgo de DoS.
- **API5 Broken Function Level Authorization**: OK. Solo GET habilitado; otros metodos devuelven 405.
- **API6 Unrestricted Access to Sensitive Business Flows**: No aplica (solo lectura).
- **API7 SSRF**: No aplica (sin llamadas salientes).
- **API8 Security Misconfiguration**: OK en general (debug off, CORS restringido, headers de seguridad). HALLAZGO verificado con curl: el codigo intenta eliminar la cabecera `Server` pero esta sigue apareciendo (`Server: Werkzeug/3.1.8 Python/3.12.3`) porque el servidor de desarrollo de Werkzeug la agrega fuera del objeto `Response` de Flask. En produccion debe desplegarse detras de un WSGI de produccion (gunicorn) y un proxy inverso que no exponga el banner.
- **API9 Improper Inventory Management**: OK. Solo 2 endpoints, documentados en el docstring del modulo.
- **API10 Unsafe Consumption of APIs**: No aplica (no consume APIs de terceros).

## 4. Respuestas obtenidas con curl

Todas las pruebas se ejecutaron contra `http://127.0.0.1:5000` con la app corriendo localmente (`python app.py`) y el token de prueba de la seccion 2.

1. `GET /health` (sin token, publico) → `200 OK`, ver `evidencias/EVI-2026-08-17-02-curl-health.txt`. Se confirman todas las cabeceras de seguridad configuradas.
2. `GET /usuarios` sin cabecera `Authorization` → `401 Unauthorized`, `{"error":"No autorizado"}`.
3. `GET /usuarios` con token invalido → `401 Unauthorized`, `{"error":"No autorizado"}`.
4. `GET /usuarios` con token valido → `200 OK`, lista completa de 3 usuarios.
5. `GET /usuarios?id=2` con token valido → `200 OK`, un unico usuario (Luis Gomez).
6. `GET /usuarios?id=1;DROP` con token valido (intento de inyeccion en el parametro) → `400 Bad Request`, `{"error":"Parametro 'id' invalido"}`. La validacion con regex rechaza el valor antes de procesarlo.

Detalle completo en `evidencias/EVI-2026-08-17-03-curl-token.txt`.

## 5. Evidencias registradas

| Archivo | Descripcion |
|---|---|
| `evidencias/EVI-2026-08-17-01-app.py` | Codigo fuente de la API en el momento de las pruebas. |
| `evidencias/EVI-2026-08-17-02-curl-health.txt` | Respuesta de `GET /health` con `curl -i`. |
| `evidencias/EVI-2026-08-17-03-curl-token.txt` | Accesos a `/usuarios` sin token, con token invalido y con token valido (incluye filtro por id e intento de inyeccion). |
| `evidencias/EVI-2026-08-17-04-revision-api.png` | Revision del codigo contra el OWASP API Security Top 10 (2023) realizada con asistencia de IA. |
