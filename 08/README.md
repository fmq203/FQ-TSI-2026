# Actividad 08 — Escaneo de seguridad web con OWASP ZAP

Analiza (DAST) la API de la Actividad 4 (`../04/app.py`) con OWASP ZAP en
modo headless vía Docker (no se usó la app de escritorio de ZAP: este
entorno no tiene interfaz gráfica).

## Cómo reproducir

```bash
# 1) Levantar la API objetivo
cd ../04
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export API_TOKEN=$(python -c 'import secrets;print(secrets.token_urlsafe(32))')
python app.py &
curl http://localhost:5000/health

# 2) Escanear con ZAP (spider + active scan)
cd ../08
docker pull ghcr.io/zaproxy/zaproxy:stable

# Endpoint protegido — el token se inyecta como header en cada petición vía el Replacer add-on
docker run --rm --network=host -v "$(pwd)/evidencias:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py \
  -t "http://localhost:5000/usuarios?id=1" \
  -r zap-report-usuarios.html -J zap-report-usuarios.json -I \
  -z "-config replacer.full_list(0).description=auth -config replacer.full_list(0).enabled=true -config replacer.full_list(0).matchtype=REQ_HEADER -config replacer.full_list(0).matchstr=Authorization -config replacer.full_list(0).regex=false -config replacer.full_list(0).replacement=Bearer\ $API_TOKEN"

# Endpoint público
docker run --rm --network=host -v "$(pwd)/evidencias:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py \
  -t "http://localhost:5000/health" -r zap-report-health.html -J zap-report-health.json -I
```

**Nota:** como es una API JSON pura sin páginas HTML, el spider clásico de
ZAP no descubre rutas por sí solo — hay que apuntarlo directamente a cada
endpoint (`-t`). Detalle en [bitacora.md](bitacora.md), sección 2.

Resultados y análisis en [bitacora.md](bitacora.md) e [informe.md](informe.md);
evidencias y reportes de ZAP en [evidencias/](evidencias/).
