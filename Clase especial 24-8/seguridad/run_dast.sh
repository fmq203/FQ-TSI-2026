#!/usr/bin/env bash
# Analisis dinamico (DAST) con OWASP ZAP baseline scan, contra ambos sistemas ya corriendo.
# Requiere Docker y las apps levantadas en :8001 y :8002 (ver README de cada sistema).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dast

docker run --rm -t --network host \
  -v "$(pwd)/dast:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://localhost:8001/login -r turnos-zap-report.html || true

docker run --rm -t --network host \
  -v "$(pwd)/dast:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://localhost:8002/login -r facturacion-zap-report.html || true

echo "Reportes generados en seguridad/dast/"
