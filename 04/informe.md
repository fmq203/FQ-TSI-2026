# Informe - Actividad 04: API REST segura (Flask)

## 1. Descripcion de la API y sus endpoints

La API simula un servicio de una institucion financiera que expone un
directorio interno de usuarios. Esta construida en Flask y define dos
endpoints:

- **`GET /health`**: endpoint publico de estado (liveness check), no expone
  informacion sensible, usado por sistemas de monitoreo.
- **`GET /usuarios`**: endpoint protegido que devuelve la lista de usuarios
  (`id`, `nombre`, `email`). Admite un parametro opcional `?id=` para
  consultar un usuario puntual. Requiere autenticacion mediante token Bearer.

No hay endpoints de escritura (POST/PUT/DELETE); cualquier otro metodo
sobre las rutas existentes responde `405 Metodo no permitido`, y cualquier
ruta inexistente responde `404 Recurso no encontrado`, ambos con un cuerpo
JSON generico que no filtra detalles internos.

## 2. Controles de seguridad implementados

- **Autenticacion por token**: `/usuarios` exige `Authorization: Bearer <token>`.
  El token se lee de la variable de entorno `API_TOKEN` (nunca hardcodeado)
  y se compara con `secrets.compare_digest` para evitar timing attacks.
- **Validacion de entrada**: el parametro `id` se valida contra la expresion
  regular `^\d{1,10}$` antes de usarse, rechazando con `400` cualquier valor
  que no sea un entero corto (mitiga intentos de inyeccion en el parametro).
- **Minimizacion de datos expuestos**: las respuestas solo incluyen los
  campos necesarios (`id`, `nombre`, `email`), sin datos sensibles.
- **CORS restringido**: solo el origen `https://app.mibanco.com`, solo
  metodo `GET`, sin credenciales (`supports_credentials=False`).
- **Cabeceras de seguridad** en toda respuesta: `X-Content-Type-Options`,
  `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`,
  `Permissions-Policy`, `Strict-Transport-Security`.
- **Modo debug deshabilitado** (`debug=False`), evitando exponer el
  depurador interactivo de Werkzeug ante una excepcion no controlada.
- **Manejadores de error genericos** para 404 y 405 que no exponen trazas
  ni detalles de implementacion.

## 3. Pruebas realizadas (con curl)

Se levanto la API localmente (`python app.py`, puerto 5000) con un token de
prueba generado con `secrets.token_urlsafe(32)`, y se ejecutaron las
siguientes pruebas (ver `bitacora.md` y `evidencias/` para el detalle
completo):

1. `curl -i http://127.0.0.1:5000/health` → `200 OK` con todas las cabeceras
   de seguridad presentes en la respuesta.
2. `curl -i http://127.0.0.1:5000/usuarios` (sin token) → `401 Unauthorized`.
3. `curl -i .../usuarios -H "Authorization: Bearer <token invalido>"` →
   `401 Unauthorized`.
4. `curl -i .../usuarios -H "Authorization: Bearer <token valido>"` →
   `200 OK` con la lista de 3 usuarios.
5. `curl -i ".../usuarios?id=2" -H "Authorization: Bearer <token valido>"` →
   `200 OK` con un unico usuario.
6. `curl -i ".../usuarios?id=1;DROP" -H "Authorization: Bearer <token valido>"`
   (intento de inyeccion en el parametro) → `400 Bad Request`, el valor es
   rechazado por la validacion con regex antes de procesarse.

Las pruebas confirman que el control de acceso, la validacion de entrada y
las cabeceras de seguridad funcionan segun lo esperado.

## 4. Hallazgos y correcciones de la revision con IA

Se realizo una revision del codigo contra el OWASP API Security Top 10
(2023) (evidencia: `evidencias/EVI-2026-08-17-04-revision-api.png`). Los
puntos evaluados como correctos (autenticacion con comparacion segura,
minimizacion de datos, CORS restringido, sin funciones administrativas
expuestas, inventario de endpoints pequeno y documentado) no requirieron
cambios. Se identificaron dos hallazgos:

1. **Falta de rate limiting (relacionado a API2 y API4 del Top 10)**: ningun
   endpoint limita la cantidad de solicitudes por cliente, lo que deja la
   API expuesta a fuerza bruta sobre el token y a agotamiento de recursos
   (DoS). **Correccion propuesta**: incorporar `flask-limiter` con un limite
   razonable por IP/token en `/usuarios`, y considerar rotacion periodica
   del token.

2. **Fuga de la cabecera `Server` (API8 - Security Misconfiguration)**: el
   codigo intenta eliminar la cabecera `Server` en `set_security_headers`
   (`response.headers.pop("Server", None)`), pero al probar con
   `curl -i` la cabecera sigue apareciendo como
   `Server: Werkzeug/3.1.8 Python/3.12.3`. Esto ocurre porque el servidor
   de desarrollo de Werkzeug agrega esa cabecera a nivel de servidor HTTP,
   fuera del objeto `Response` de Flask, por lo que el `pop()` en el
   codigo de la aplicacion no tiene efecto sobre el servidor de desarrollo.
   **Correccion propuesta**: no depender del servidor de desarrollo en
   produccion; desplegar la app detras de un servidor WSGI de produccion
   (gunicorn/uWSGI) y un proxy inverso (nginx) configurado para no exponer
   el banner del servidor real.

Ambos hallazgos fueron verificados empiricamente con las pruebas curl de la
seccion anterior antes de documentarlos, evitando reportar falsos positivos.

## 5. Entregable

- API Flask funcional: `app.py`, `requirements.txt`.
- Pruebas con curl: `bitacora.md` (seccion 4) y `evidencias/`.
- Evidencias: carpeta `evidencias/` (codigo, respuestas curl, revision OWASP).
- Este informe: `informe.md`.
