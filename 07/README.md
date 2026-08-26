# Actividad 07 — Análisis estático avanzado con Semgrep y reglas propias

Analiza el código de `sistema-turnos` y `sistema-facturacion`
(`../Clase especial 24-8/`), los mismos dos sistemas ya evaluados con Bandit
y pip-audit.

## Cómo usar
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

# Ruleset público
semgrep --config p/security-audit \
  "../Clase especial 24-8/sistema-turnos/app" \
  "../Clase especial 24-8/sistema-facturacion/app"

# Regla propia (prohíbe eval())
semgrep --config reglas/no-eval.yaml reglas/prueba_eval.py   # debe dar 1 hallazgo
semgrep --config reglas/no-eval.yaml \
  "../Clase especial 24-8/sistema-turnos/app" \
  "../Clase especial 24-8/sistema-facturacion/app"           # debe dar 0 hallazgos
```

Resultados y análisis en [bitacora.md](bitacora.md) e [informe.md](informe.md);
evidencias crudas en [evidencias/](evidencias/).
