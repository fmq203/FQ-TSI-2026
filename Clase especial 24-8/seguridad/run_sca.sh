#!/usr/bin/env bash
# Analisis de composicion de software (SCA) con pip-audit sobre las dependencias de cada sistema.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p sca

for sistema in sistema-turnos sistema-facturacion; do
  echo "== SCA: $sistema =="
  pip-audit -r "../$sistema/requirements.txt" -f json -o "sca/${sistema}-pip-audit.json" || true
  pip-audit -r "../$sistema/requirements.txt" -f columns > "sca/${sistema}-pip-audit.txt" || true
done

echo "Reportes generados en seguridad/sca/"
