#!/usr/bin/env bash
# Genera el SBOM (CycloneDX JSON) de cada sistema desde su propio entorno virtual.
# Requiere que cada sistema tenga su venv creado con `pip install -r requirements.txt`.
set -euo pipefail
cd "$(dirname "$0")"

for sistema in sistema-turnos sistema-facturacion; do
  echo "== SBOM: $sistema =="
  source "../$sistema/venv/bin/activate"
  pip install -q cyclonedx-bom
  cyclonedx-py environment -o "sbom-${sistema}.json"
  deactivate
done

echo "SBOM generados en seguridad/../sbom/"
