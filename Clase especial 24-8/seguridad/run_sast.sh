#!/usr/bin/env bash
# Analisis estatico (SAST) con Bandit sobre ambos sistemas.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p sast

for sistema in sistema-turnos sistema-facturacion; do
  echo "== SAST: $sistema =="
  bandit -r "../$sistema/app" -f json -o "sast/${sistema}-bandit.json" || true
  bandit -r "../$sistema/app" -f txt -o "sast/${sistema}-bandit.txt" || true
done

echo "Reportes generados en seguridad/sast/"
