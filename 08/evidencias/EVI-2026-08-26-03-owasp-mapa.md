# EVI-2026-08-26-03 — Alertas mapeadas al OWASP Top 10 (análisis asistido por IA)

> Nota: sustituye la captura `.png` pedida por la consigna — es el análisis
> de texto que arma la IA al pedirle "explicame estas alertas y a qué
> categoría del OWASP Top 10 pertenecen" (Paso 5/6 de la actividad).

## 1. Server Leaks Version Information via "Server" HTTP Response Header Field

- **CWE:** CWE-497 (Exposure of Sensitive System Information to an Unauthorized Control Sphere)
- **OWASP Top 10 (2021):** **A05:2021 — Security Misconfiguration**
- **Qué significa:** toda respuesta de la API incluye `Server: Werkzeug/3.1.8 Python/3.12.3`. Un atacante obtiene, sin esfuerzo, la versión exacta del framework y del intérprete — información que usa para buscar CVEs conocidas de esas versiones puntuales antes de intentar explotarlas.
- **Por qué lo encontró DAST y no SAST:** el código (`04/app.py:57-67`) sí intenta suprimir el header:
  ```python
  response.headers.pop("Server", None)
  ```
  Bandit y Semgrep, al leer ese código, no tienen forma de saber que esta línea **no tiene efecto real** en este deployment. El `Server` header no lo pone Flask ni el objeto `Response` — lo agrega el propio servidor de desarrollo de Werkzeug (`WSGIRequestHandler`) a nivel de socket HTTP, después de que `after_request` ya terminó de correr. Confirmado manualmente:
  ```
  $ curl -sI http://localhost:5000/health
  Server: Werkzeug/3.1.8 Python/3.12.3   # sigue presente
  ```
  Este es exactamente el tipo de brecha entre "intención del código" y "comportamiento real en ejecución" que solo un DAST puede detectar — Bandit/Semgrep habrían dado el código por bueno.
- **Corrección en Flask:** el `pop()` en `after_request` es inútil mientras se sirva con `werkzeug.serving` (el `app.run()` de desarrollo). La solución real es **no usar el servidor de desarrollo en producción**: desplegar detrás de un servidor WSGI (gunicorn/uWSGI) y un reverse proxy (nginx) configurado con `proxy_hide_header Server;` y `server_tokens off;`, que sí controla el header a nivel de servidor.

## 2. Cross-Origin-Resource-Policy Header Missing or Invalid

- **CWE:** CWE-693 (Protection Mechanism Failure)
- **OWASP Top 10 (2021):** **A05:2021 — Security Misconfiguration**
- **Qué significa:** `/health` no envía `Cross-Origin-Resource-Policy`. Sin este header, otros orígenes pueden incrustar la respuesta como sub-recurso (`<script src>`, `<img>`) y, en navegadores vulnerables a ataques tipo Spectre, potencialmente inferir su contenido por canal lateral. Riesgo bajo para este endpoint puntual (no devuelve datos sensibles), pero es una cabecera de defensa en profundidad ausente.
- **Corrección en Flask:** agregar `response.headers["Cross-Origin-Resource-Policy"] = "same-origin"` en el mismo `after_request` que ya fija las demás cabeceras de seguridad.

## 3. CORS Header (informativo)

- **OWASP Top 10 (2021):** relacionado a **A05:2021** solo si estuviera mal configurado.
- **Qué significa:** ZAP simplemente detectó que `/usuarios` responde con cabeceras CORS y lo reporta como informativo para revisión manual. Verificado en el código (`04/app.py:33-40`): `CORS()` está correctamente restringido a `resources={r"/usuarios": {"origins": ALLOWED_ORIGIN}}` con un único origen permitido (`https://app.mibanco.com`), método `GET` únicamente y sin credenciales. **No es una vulnerabilidad** — es el comportamiento esperado y deseado.

## 4. Non-Storable Content / Storable and Cacheable Content (informativo)

- **CWE:** CWE-524 (Information Exposure Through Caching)
- **OWASP Top 10 (2021):** no aplica como hallazgo — nota de buenas prácticas, no vulnerabilidad.
- **Qué significa:** ZAP marca `/` y `/usuarios` como no cacheables (correcto por defecto, ya que las respuestas van con `Authorization` y sin `Cache-Control: public`), y `/health` como cacheable (correcto también, es un endpoint público sin datos sensibles). No requiere acción.

## Resumen de mapeo

| Alerta | OWASP Top 10 2021 | ¿Requiere acción? |
|---|---|---|
| Server header leak | A05 — Security Misconfiguration | Sí (ver plan de remediación) |
| CORP header ausente en `/health` | A05 — Security Misconfiguration | Sí, bajo costo |
| CORS Header (informativo) | — | No, configuración correcta |
| Non-Storable/Storable Content | — | No, comportamiento esperado |

## ¿Qué encontró ZAP que Bandit/Semgrep no podían ver?

El hallazgo #1 es la respuesta directa a la pregunta de reflexión de la
consigna: **el gap entre lo que el código dice que hace y lo que el
servidor realmente envía por la red.** Bandit y Semgrep (Actividad 07)
analizan el árbol de sintaxis del código Python; ambos habrían leído
`response.headers.pop("Server", None)` como una mitigación correcta y no
habrían generado ninguna alerta ahí. Solo enviando una petición HTTP real
contra la aplicación en ejecución (DAST) se descubre que esa línea no
alcanza, porque el header lo inyecta una capa por debajo del control de la
aplicación (el servidor de desarrollo de Werkzeug). SAST audita intención;
DAST audita comportamiento observable — y en este caso difieren.
