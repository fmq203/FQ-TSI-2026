# EVI-2026-08-26-04 — Plan de remediación priorizado

> Sustituye la captura `.png` pedida por la consigna, respondiendo el
> prompt sugerido: "Dame un plan de remediación priorizado para las alertas
> de un escaneo DAST de una API financiera".

## Criterio de priorización

Para una API financiera, prioridad = **explotabilidad real** (¿hay dato
sensible o control de acceso involucrado?) × **costo de la corrección**.
Con 0 hallazgos Alto/Medio, ninguno es bloqueante para producción, pero
ambos Low quedan priorizados por ser correcciones de bajo costo con
beneficio de defensa en profundidad — exactamente el tipo de deuda que en
una entidad financiera conviene cerrar antes de que se acumule.

| Prioridad | ID | Hallazgo | Severidad | Acción correctiva | Esfuerzo | Responsable | Plazo |
|---|---|---|---|---|---|---|---|
| **1** | DAST-01 | Server leaks version info (`Server` header) | Low | Migrar de `app.run()` (servidor de desarrollo Werkzeug) a un servidor WSGI de producción (gunicorn/uWSGI) detrás de nginx con `proxy_hide_header Server;` / `server_tokens off;`. El `response.headers.pop("Server")` actual en el código se mantiene como defensa adicional pero no es suficiente por sí solo. | Bajo–Medio (cambio de infraestructura de despliegue, no de lógica de negocio) | Equipo de desarrollo / DevOps | Antes de cualquier despliegue a producción — hoy corre con el servidor de desarrollo, que además de este leak no está pensado para carga real |
| **2** | DAST-02 | `Cross-Origin-Resource-Policy` ausente en `/health` | Low | Agregar `response.headers["Cross-Origin-Resource-Policy"] = "same-origin"` en `set_security_headers()` (`04/app.py:57`), junto a las demás cabeceras ya presentes | Muy bajo (una línea) | Equipo de desarrollo | Próximo sprint |
| — | DAST-03 | CORS Header (informativo) | Informational | Ninguna — configuración ya correcta (origen único, sin credenciales). Mantener bajo revisión si se agregan nuevos orígenes o endpoints. | — | — | Aceptado, sin acción |
| — | DAST-04 | Non-Storable/Storable Content (informativo) | Informational | Ninguna — comportamiento de caché correcto para cada endpoint según su sensibilidad. | — | — | Aceptado, sin acción |

## Nota sobre el hallazgo de mayor prioridad

DAST-01 no es solo "un header de más": es la evidencia de que la API
todavía corre con `app.run(debug=False)`, el servidor de desarrollo de
Flask/Werkzeug, que **no está diseñado para producción** (single-threaded
por defecto, sin manejo robusto de conexiones concurrentes, y como se
confirmó acá, sin control real sobre las cabeceras de bajo nivel). El plan
de remediación real no es "esconder el header" sino "cambiar de servidor
antes de exponer esto a tráfico real" — el header leak es el síntoma que
lo hizo visible en este escaneo.

## Retesting

Una vez aplicada la corrección DAST-01 (migración a gunicorn/nginx),
volver a correr:
```bash
docker run --rm --network=host -v "$(pwd)/evidencias:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py -t http://localhost:5000/health -I
```
y confirmar que `curl -sI http://localhost:5000/health` ya no incluye
`Server: Werkzeug/...`. Documentar el resultado en la sección 5 de
`../informe.md`.
