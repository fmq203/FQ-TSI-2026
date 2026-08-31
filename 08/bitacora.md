# Bitácora RSI — Actividad 08: Escaneo de seguridad web con OWASP ZAP

**Fecha:** 2026-08-26
**Objetivo escaneado:** API de la Actividad 4 (`../04/app.py`), Flask,
corriendo en `http://localhost:5000` (`/health` público, `/usuarios`
protegido con Bearer token).
**Herramienta:** OWASP ZAP (imagen oficial `ghcr.io/zaproxy/zaproxy:stable`,
vía Docker, modo headless — no hay entorno gráfico disponible en esta
sesión).

## 1. Levantar la API

```bash
cd ../04
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export API_TOKEN=$(python -c 'import secrets;print(secrets.token_urlsafe(32))')
python app.py &
curl http://localhost:5000/health   # {"status":"ok"}
```

## 2. Spider — nota metodológica importante

El spider clásico de ZAP rastrea `<a href>` en páginas HTML. La API de la
Actividad 4 es JSON puro, sin ninguna página para rastrear, así que apuntar
ZAP a la raíz (`http://localhost:5000`) no descubrió ningún endpoint real
(solo probó defaults como `/robots.txt`, todos 404). Para que el active
scan atacara `/health` y `/usuarios` de verdad, se lanzaron escaneos
apuntando **directamente a cada endpoint** conocido por el código —
técnica necesaria para escanear APIs sin frontend cuando no se dispone de
una especificación OpenAPI/Swagger para importar.

## 3. Active Scan

Tres corridas con `zap-full-scan.py` (incluye spider + active scan):

```bash
# Endpoint protegido, con token inyectado vía Replacer add-on de ZAP
docker run --rm --network=host -v "$(pwd)/evidencias:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py \
  -t "http://localhost:5000/usuarios?id=1" \
  -r zap-report-usuarios.html -J zap-report-usuarios.json -I \
  -z "-config replacer.full_list(0).description=auth ... -config replacer.full_list(0).replacement=Bearer $API_TOKEN"

# Endpoint público
docker run --rm --network=host -v "$(pwd)/evidencias:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py \
  -t "http://localhost:5000/health" -r zap-report-health.html -J zap-report-health.json -I
```

~140 reglas activas ejecutadas por objetivo (SQLi, XSS reflejado/persistente/DOM,
SSRF, XXE, path traversal, command injection, NoSQL injection, SSTI, etc.)

## 4. Alertas encontradas y su severidad

| Alerta | Riesgo | Endpoint(s) |
|---|---|---|
| Server Leaks Version Information via "Server" header | **Low (High confidence)** | Todos |
| Cross-Origin-Resource-Policy Header Missing | **Low (Medium confidence)** | `/health` |
| CORS Header | Informational | `/usuarios` |
| Non-Storable / Storable Content | Informational | Todos |

**0 Alto, 0 Medio, 2 Bajo, 2 Informativo.** Detalle completo:
[`evidencias/EVI-2026-08-26-01-zap-alertas.md`](evidencias/EVI-2026-08-26-01-zap-alertas.md).

## 5. Asociación alerta → OWASP Top 10

Ambos hallazgos Low mapean a **A05:2021 — Security Misconfiguration**.
Interpretación completa, con la explicación de por qué el hallazgo del
header `Server` es un caso de libro de "algo que SAST no puede ver":
[`evidencias/EVI-2026-08-26-03-owasp-mapa.md`](evidencias/EVI-2026-08-26-03-owasp-mapa.md).

## 6. Plan de remediación

Prioridad 1: migrar del servidor de desarrollo de Flask/Werkzeug a un
servidor WSGI de producción (gunicorn + nginx) — el leak del header
`Server` es síntoma de que la API sigue corriendo con `app.run()`, no apto
para producción. Prioridad 2: agregar `Cross-Origin-Resource-Policy` a las
cabeceras de seguridad ya centralizadas en `set_security_headers()`. Plan
completo con esfuerzo y responsables:
[`evidencias/EVI-2026-08-26-04-remediacion.md`](evidencias/EVI-2026-08-26-04-remediacion.md).

## 7. Reporte exportado y evidencias guardadas

- `evidencias/EVI-2026-08-26-01-zap-alertas.md` — alertas consolidadas de los 3 escaneos.
- `evidencias/EVI-2026-08-26-02a-zap-reporte-raiz.html`, `-02b-...-usuarios.html`, `-02c-...-health.html` — reportes HTML nativos de ZAP, uno por escaneo.
- `evidencias/EVI-2026-08-26-03-owasp-mapa.md` — mapeo a OWASP Top 10.
- `evidencias/EVI-2026-08-26-04-remediacion.md` — plan de remediación.
- Reportes JSON/MD crudos de cada escaneo (`zap-reporte-*.json/.md`) como respaldo técnico adicional.

## 8. Reflexión sobre el uso de IA

**¿Por qué conviene combinar SAST y DAST?** Porque auditan capas distintas:
SAST lee la intención del código; DAST observa el comportamiento real del
sistema desplegado. Este escaneo lo demostró de forma concreta: el código
de `04/app.py` intenta explícitamente remover el header `Server`
(`response.headers.pop("Server", None)`), y tanto Bandit como Semgrep
(Actividad 07) habrían dado por buena esa línea — ninguna de las dos
herramientas ejecuta el código, solo lo leen. Únicamente al mandar una
petición HTTP real contra la app corriendo se descubrió que el header
sigue presente, porque lo agrega el servidor de desarrollo de Werkzeug a
nivel de socket, después de que el código de la aplicación ya terminó de
correr. **Esa es la vulnerabilidad que solo aparece en ejecución**: no es
un patrón de código inseguro, es un gap entre lo que el desarrollador
programó y lo que la infraestructura de despliegue realmente permite.

## 9. Verificación manual (2026-08-31)

El estudiante reprodujo el escaneo manualmente, paso a paso, ejecutando él
mismo cada comando (levantar la API, spider, active scan sobre `/health` y
`/usuarios`) en lugar de que se corriera de forma automatizada:

1. **Spider clásico contra la raíz** (`zap-baseline.py -t http://localhost:5000`):
   confirmó en vivo la limitación ya documentada en la sección 2 — encontró
   únicamente 3 URLs sintéticas (`/`, `/robots.txt`, `/sitemap.xml`), todas
   404, sin descubrir `/health` ni `/usuarios`.
   Evidencia: [`evidencias/EVI-2026-08-31-01-zap-spider-demo.json`](evidencias/EVI-2026-08-31-01-zap-spider-demo.json).
2. **Active scan sobre `/health`**: 200 OK, **2 alertas Low** (Server header,
   Cross-Origin-Resource-Policy) — idéntico al hallazgo original.
   Evidencia: [`evidencias/EVI-2026-08-31-02a-zap-reporte-health.html`](evidencias/EVI-2026-08-31-02a-zap-reporte-health.html).
3. **Active scan sobre `/usuarios?id=1`** con el token inyectado vía Replacer:
   200 OK, **1 alerta Low** (Server header). Confirma que el mecanismo de
   autenticación vía header `Authorization: Bearer` funciona correctamente
   contra el escaneo activo.
   Evidencia: [`evidencias/EVI-2026-08-31-02b-zap-reporte-usuarios.html`](evidencias/EVI-2026-08-31-02b-zap-reporte-usuarios.html).

**Resultado:** los hallazgos son consistentes con la corrida del
2026-08-26 (0 Alto, 0 Medio, 2 Bajo) — no hubo regresiones ni hallazgos
nuevos entre ambas fechas. Repaldos JSON crudos de esta corrida:
`evidencias/zap-reporte-health-manual.json`,
`evidencias/zap-reporte-usuarios-manual.json`.
