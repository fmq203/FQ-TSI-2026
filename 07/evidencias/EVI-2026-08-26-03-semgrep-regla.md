# EVI-2026-08-26-03 — Ejecución de la regla propia `no-eval.yaml`

Regla probada en dos pasos: primero contra un archivo de prueba con
`eval()` deliberado, luego contra el código real de ambos sistemas.

## 1. Contra el archivo de prueba (`reglas/prueba_eval.py`)

**Comando:**
```bash
semgrep --config reglas/no-eval.yaml reglas/prueba_eval.py
```

| Métrica | Valor |
|---|---|
| Reglas aplicadas | 1 |
| Archivos escaneados | 1 |
| Hallazgos | **1** (1 bloqueante) |

### Hallazgo — `reglas/prueba_eval.py:10`

- **Regla:** `reglas.no-eval-python`
- **Severidad:** Blocking

> Uso de eval() detectado. eval() ejecuta código arbitrario en tiempo de
> ejecución y es una vía directa a Remote Code Execution (RCE) si el
> argumento incluye, aunque sea parcialmente, entrada de usuario. Prohibido
> por norma interna del equipo de seguridad (RSI). Reemplazar por
> `ast.literal_eval()` (si solo se necesita parsear literales de Python) o
> por una función de mapeo/parsing explícita para el caso de uso real.

```python
10┆ return eval(expresion_usuario)
```

**Resultado:** ✅ la regla detecta correctamente el patrón prohibido.

## 2. Contra el código real de ambos sistemas

**Comando:**
```bash
semgrep --config reglas/no-eval.yaml \
  "../Clase especial 24-8/sistema-turnos/app" \
  "../Clase especial 24-8/sistema-facturacion/app"
```

| Métrica | Valor |
|---|---|
| Reglas aplicadas | 1 |
| Archivos escaneados | 28 |
| Hallazgos | **0** |

**Resultado:** ✅ confirma que ninguno de los dos sistemas usa `eval()`, sin
falsos positivos sobre el código de producción.

<details>
<summary>Salida cruda de la terminal (semgrep)</summary>

```text
=== 1) Regla propia contra el archivo de prueba (reglas/prueba_eval.py) ===

┌─────────────┐
│ Scan Status │
└─────────────┘
  Scanning 1 file with 1 Code rule:
  Scanning 1 file.

┌──────────────┐
│ Scan Summary │
└──────────────┘
✅ Scan completed successfully.
 • Findings: 1 (1 blocking)
 • Rules run: 1
 • Targets scanned: 1
 • Parsed lines: ~100.0%
 • No ignore information available
Ran 1 rule on 1 file: 1 finding.

┌────────────────┐
│ 1 Code Finding │
└────────────────┘

    reglas/prueba_eval.py
   ❯❯❱ reglas.no-eval-python
          ❰❰ Blocking ❱❱
          Uso de eval() detectado. eval() ejecuta código arbitrario en tiempo de ejecución y es una vía
          directa a Remote Code Execution (RCE) si el argumento incluye, aunque sea parcialmente, entrada de
          usuario. Prohibido por norma interna del equipo de seguridad (RSI). Reemplazar por
          ast.literal_eval() (si solo se necesita parsear literales de Python) o por una función de
          mapeo/parsing explícita para el caso de uso real.

           10┆ return eval(expresion_usuario)


=== 2) Regla propia contra el código real de ambos sistemas (Clase especial 24-8) ===

┌─────────────┐
│ Scan Status │
└─────────────┘
  Scanning 70 files with 1 Code rule:
  Scanning 28 files.

┌──────────────┐
│ Scan Summary │
└──────────────┘
✅ Scan completed successfully.
 • Findings: 0 (0 blocking)
 • Rules run: 1
 • Targets scanned: 28
 • Parsed lines: ~100.0%
 • No ignore information available
Ran 1 rule on 28 files: 0 findings.
If Semgrep missed a finding, please send us feedback to let us know!
See https://semgrep.dev/docs/reporting-false-negatives/
```

</details>
