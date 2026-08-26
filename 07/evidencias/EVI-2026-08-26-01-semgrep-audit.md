# EVI-2026-08-26-01 — Ejecución de Semgrep con `p/security-audit`

**Comando:**
```bash
semgrep --config p/security-audit \
  "../Clase especial 24-8/sistema-turnos/app" \
  "../Clase especial 24-8/sistema-facturacion/app"
```

## Resumen del scan

| Métrica | Valor |
|---|---|
| Reglas descargadas | 225 (9 multi-lenguaje + 77 Python, origen Community) |
| Reglas aplicadas según lenguaje presente | 86 |
| Archivos escaneados | 70 |
| Hallazgos | 2 (2 bloqueantes) |
| Líneas parseadas | ~100% |

## Hallazgos

### 1. `sistema-facturacion/app/templates/mfa_show.html:8`

- **Regla:** `generic.html-templates.security.var-in-href.var-in-href`
- **Severidad:** Blocking
- **Detalle:** [https://sg.run/x1kP](https://sg.run/x1kP)

> Detected a template variable used in an anchor tag with the 'href'
> attribute. This allows a malicious actor to input the 'javascript:' URI
> and is subject to cross-site scripting (XSS) attacks. If using Flask, use
> `url_for()` to safely generate a URL. If using Django, use the `url`
> filter to safely generate a URL. If using Mustache, use a URL encoding
> library, or prepend a slash '/' to the variable for relative links
> (`href="/{{link}}"`). You may also consider setting the Content Security
> Policy (CSP) header.

```html
8┆ <a href="{{ volver }}"><button type="button">Volver a ingresar el código</button></a>
```

### 2. `sistema-turnos/app/templates/mfa_show.html:8`

- **Regla:** `generic.html-templates.security.var-in-href.var-in-href`
- **Severidad:** Blocking
- **Detalle:** [https://sg.run/x1kP](https://sg.run/x1kP)

Mismo patrón y misma línea que el hallazgo anterior (template compartido
entre ambos sistemas):

```html
8┆ <a href="{{ volver }}"><button type="button">Volver a ingresar el código</button></a>
```

## Interpretación y comparación con Bandit

Ver análisis completo en [`EVI-2026-08-26-04-comparacion.md`](EVI-2026-08-26-04-comparacion.md).

<details>
<summary>Salida cruda de la terminal (semgrep)</summary>

```text
┌─────────────┐
│ Scan Status │
└─────────────┘
  Scanning 70 files with 225 Code rules:

  Language      Rules   Files          Origin      Rules
 ─────────────────────────────        ───────────────────
  <multilang>       9      42          Community     225
  python           77      28

┌──────────────┐
│ Scan Summary │
└──────────────┘
✅ Scan completed successfully.
 • Findings: 2 (2 blocking)
 • Rules run: 86
 • Targets scanned: 70
 • Parsed lines: ~100.0%
 • No ignore information available
Ran 86 rules on 70 files: 2 findings.

┌─────────────────┐
│ 2 Code Findings │
└─────────────────┘

    ../Clase especial 24-8/sistema-facturacion/app/templates/mfa_show.html
    ❯❱ generic.html-templates.security.var-in-href.var-in-href
          ❰❰ Blocking ❱❱
          Detected a template variable used in an anchor tag with the 'href' attribute. This allows a
          malicious actor to input the 'javascript:' URI and is subject to cross- site scripting (XSS)
          attacks. If using Flask, use 'url_for()' to safely generate a URL. If using Django, use the 'url'
          filter to safely generate a URL. If using Mustache, use a URL encoding library, or prepend a slash
          '/' to the variable for relative links (`href="/{{link}}"`). You may also consider setting the
          Content Security Policy (CSP) header.
          Details: https://sg.run/x1kP

            8┆ <a href="{{ volver }}"><button type="button">Volver a ingresar el código</button></a>

    ../Clase especial 24-8/sistema-turnos/app/templates/mfa_show.html
    ❯❱ generic.html-templates.security.var-in-href.var-in-href
          ❰❰ Blocking ❱❱
          Detected a template variable used in an anchor tag with the 'href' attribute. This allows a
          malicious actor to input the 'javascript:' URI and is subject to cross- site scripting (XSS)
          attacks. If using Flask, use 'url_for()' to safely generate a URL. If using Django, use the 'url'
          filter to safely generate a URL. If using Mustache, use a URL encoding library, or prepend a slash
          '/' to the variable for relative links (`href="/{{link}}"`). You may also consider setting the
          Content Security Policy (CSP) header.
          Details: https://sg.run/x1kP

            8┆ <a href="{{ volver }}"><button type="button">Volver a ingresar el código</button></a>
```

</details>
