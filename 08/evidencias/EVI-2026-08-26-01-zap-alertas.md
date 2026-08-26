# EVI-2026-08-26-01 — Listado de alertas de OWASP ZAP por severidad

> Nota: la consigna pide una captura de pantalla (`.png`) de la UI de ZAP.
> Este escaneo se ejecutó en modo headless (`zap-full-scan.py` vía Docker,
> sin interfaz gráfica disponible en este entorno), así que esta evidencia
> es el listado real de alertas extraído de los reportes JSON/HTML
> exportados por ZAP, no una captura de pantalla.

## Contexto técnico: por qué se corrieron 3 escaneos en vez de 1

La API de la Actividad 4 (`04/app.py`) es una API REST pura que devuelve
JSON, sin ninguna página HTML con enlaces. El **spider clásico de ZAP**
funciona rastreando `<a href>` de páginas HTML — al apuntarlo a
`http://localhost:5000` no encontró nada para seguir (0 enlaces), así que
el *active scan* solo atacó la URL raíz y algunos paths por defecto
(`/`, `/robots.txt`, `/sitemap.xml`), todos 404.

Para que el active scan realmente atacara los dos endpoints reales, se
apuntó `zap-full-scan.py` directamente a cada uno como target:

| Escaneo | Target | Autenticación | Reporte |
|---|---|---|---|
| Raíz | `http://localhost:5000` | — | `zap-reporte-raiz.{html,json,md}` |
| Usuarios | `http://localhost:5000/usuarios?id=1` | Header `Authorization: Bearer <API_TOKEN>` inyectado vía Replacer add-on | `zap-reporte-usuarios.{html,json,md}` |
| Health | `http://localhost:5000/health` | — (endpoint público) | `zap-reporte-health.{html,json,md}` |

Esto en sí mismo es un hallazgo metodológico: en una API sin frontend, el
spider tradicional de ZAP no sirve para descubrir rutas — hace falta una
especificación (OpenAPI/Swagger) o, como acá, apuntar el escaneo
directamente a cada endpoint conocido por el código.

## Alertas consolidadas (los 3 escaneos, deduplicadas)

| # | Alerta | Riesgo (Confianza) | CWE | Endpoint(s) donde aparece | Instancias |
|---|---|---|---|---|---|
| 1 | Server Leaks Version Information via "Server" HTTP Response Header Field | **Low (High)** | CWE-497 | Los 3 escaneos — presente en **toda** respuesta (`/`, `/health`, `/usuarios`) | 4 por escaneo |
| 2 | Cross-Origin-Resource-Policy Header Missing or Invalid | **Low (Medium)** | CWE-693 | `/health` | 1 |
| 3 | CORS Header | Informational (High) | — | `/usuarios?id=1` | 1 |
| 4 | Non-Storable Content / Storable and Cacheable Content | Informational (Medium) | CWE-524 | Raíz y `/usuarios` (Non-Storable); `/health` (Storable) | 4 |

**Resumen por severidad:** 0 Alto, 0 Medio, 2 Bajo, 2 Informativo.

## Reglas activas ejecutadas sin hallazgo (selección relevante)

El active scan corrió ~140 reglas por objetivo (inyección SQL, XSS
reflejado/persistente/DOM, SSRF, XXE, path traversal, command injection,
NoSQL injection, SSTI, Log4Shell, Spring4Shell, etc.) — todas en **PASS**
(sin hallazgo) contra `/usuarios?id=1`, incluyendo específicamente:

- `SQL Injection` (y variantes MySQL/PostgreSQL/Oracle/MsSQL/Hypersonic time-based)
- `Cross Site Scripting (Reflected/Persistent/DOM Based)`
- `Path Traversal`, `Remote OS Command Injection`
- `NoSQL Injection - MongoDB`

Esto confirma en tiempo de ejecución lo que ya sugería el código: el
parámetro `id` de `/usuarios` está validado contra `ID_PATTERN = r"^\d{1,10}$"`
antes de usarse, así que no hay superficie de inyección real ahí.

Detalle completo de cada alerta, con `solution` y evidencia técnica cruda,
en los reportes HTML/JSON de cada escaneo (mismo directorio).
