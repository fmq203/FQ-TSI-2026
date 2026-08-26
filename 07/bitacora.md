# Bitácora RSI — Actividad 07: Análisis estático avanzado con Semgrep y reglas propias

**Fecha:** 2026-08-26
**Código analizado:** `sistema-turnos/app` y `sistema-facturacion/app`
(`../Clase especial 24-8/`), los mismos dos sistemas ya evaluados con Bandit
y pip-audit el 2026-08-24.
**Entorno:** venv propio (`07/venv`), `semgrep 1.174.0`.

## 1. Instalación y ejecución

```bash
python3 -m venv venv && source venv/bin/activate
pip install semgrep
semgrep --version   # 1.174.0
```

Corrida con el ruleset público `p/security-audit` contra ambos sistemas:

```bash
semgrep --config p/security-audit \
  "../Clase especial 24-8/sistema-turnos/app" \
  "../Clase especial 24-8/sistema-facturacion/app"
```

Resultado: 86 reglas ejecutadas sobre 70 archivos (Python + HTML/Jinja),
**2 hallazgos**. Evidencia completa: [`evidencias/EVI-2026-08-26-01-semgrep-audit.md`](evidencias/EVI-2026-08-26-01-semgrep-audit.md).

## 2. Hallazgos de Semgrep interpretados

- `generic.html-templates.security.var-in-href.var-in-href` en
  `sistema-turnos/app/templates/mfa_show.html:8` y
  `sistema-facturacion/app/templates/mfa_show.html:8` — variable de plantilla
  (`{{ volver }}`) interpolada dentro de un atributo `href` sin escapar,
  patrón asociado a **CWE-79 (XSS)**.
- Se rastreó el origen del dato (`app/routers/auth_web.py:115`): es una
  constante del servidor (`"/mfa/verify"` o `"/mfa/setup"`), no un valor de
  usuario. No es explotable con el código actual, pero es un patrón frágil
  que se vuelve una XSS real en cuanto se reutilice la plantilla con un
  input externo. Análisis completo en
  [`evidencias/EVI-2026-08-26-04-comparacion.md`](evidencias/EVI-2026-08-26-04-comparacion.md).

## 3. Comparación Bandit vs Semgrep

| | Bandit (2026-08-24) | Semgrep `p/security-audit` (hoy) |
|---|---|---|
| Alcance | Solo `.py` | `.py` + `.html`/Jinja |
| Hallazgo `random.uniform` (CWE-330, VULN-001) | Sí | No |
| Hallazgo XSS en `mfa_show.html` (CWE-79) | No puede verlo (no analiza HTML) | Sí |

Las dos herramientas se complementan: Bandit no tiene forma estructural de
ver un problema en una plantilla HTML, y el ruleset de Semgrep usado hoy no
incluyó el patrón de `random` inseguro que Bandit sí trae por defecto
(`B311`). Ninguna cubre el 100% de la superficie por sí sola.

## 4. Regla propia escrita y probada

Regla `reglas/no-eval.yaml` (`no-eval-python`, severidad `ERROR`,
CWE-95 — Eval Injection), copiada como evidencia en
[`evidencias/EVI-2026-08-26-02-regla-no-eval.yaml`](evidencias/EVI-2026-08-26-02-regla-no-eval.yaml).

Prueba en dos pasos (evidencia completa:
[`evidencias/EVI-2026-08-26-03-semgrep-regla.md`](evidencias/EVI-2026-08-26-03-semgrep-regla.md)):

1. Contra `reglas/prueba_eval.py` (archivo de prueba creado para esta
   actividad, con un `eval()` deliberado) → **1 hallazgo**, la regla detecta
   correctamente el patrón.
2. Contra el código real de ambos sistemas → **0 hallazgos**: se confirma
   que ninguno de los dos sistemas usa `eval()`, sin falsos positivos.

## 5. Decisión sobre integrar Semgrep al flujo de trabajo

**Decisión: integrar.** Se incorpora `semgrep --config p/security-audit` y
`semgrep --config reglas/no-eval.yaml` (esta última bloqueante, severidad
`ERROR`) como paso de CI adicional a Bandit, no en reemplazo — cubren
superficies distintas (ver comparación arriba). La regla propia queda como
base de una carpeta `reglas/` versionada del equipo, a la que se le
agregarán reglas específicas de la institución a medida que se identifiquen
(ver propuestas en
[`evidencias/EVI-2026-08-26-04-comparacion.md`](evidencias/EVI-2026-08-26-04-comparacion.md), sección 3).

## 6. Reflexión sobre el uso de IA

¿Por qué un RSI debería poder escribir reglas de análisis para el equipo?
Porque el conocimiento de "qué es inseguro en nuestro contexto" vive en el
RSI y en el equipo de seguridad, no en un ruleset genérico descargado de
internet. Escribir la regla propia en YAML fue rápido justamente porque el
patrón (`eval(...)`) es simple, pero el mismo mecanismo escala a reglas que
codifican convenciones internas del banco (ver ejemplos en la sección 3 del
análisis comparativo) — cosas que ningún ruleset público podría conocer.
Reglas que prohibiría en esta organización, además de `eval()`: logging de
variables con nombres de campos sensibles (`password`, `token`, `documento`,
`tarjeta`), queries SQL armadas por concatenación/f-string en vez de
parámetros bindeados, y cualquier endpoint bajo `/api/v1/` que toque una
tabla de negocio sin pasar por el decorator interno de autorización.
