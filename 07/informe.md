# Informe Ejecutivo — Actividad 07: Análisis Estático Avanzado con Semgrep y Reglas Propias

**Institución:** Banco Ficticio del Uruguay (ejercicio académico)
**Responsable de Seguridad de la Información (RSI):** [Nombre y cargo]
**Destinatario:** Banco Central del Uruguay — Superintendencia de Instituciones Financieras
**Asunto:** Análisis estático avanzado (SAST) con Semgrep sobre Sistema de Turnos y Sistema de Facturación, y definición de regla propia de seguridad
**Fecha:** 2026-08-26 | **Versión:** 1.0 | **Clasificación:** Confidencial

## 1. Resumen ejecutivo

Se instaló Semgrep (SAST de código abierto) y se ejecutó el ruleset público
`p/security-audit` sobre el código fuente de los dos sistemas evaluados
previamente con Bandit (2026-08-24): Sistema de Turnos y Sistema de
Facturación. A diferencia de Bandit, que solo analiza código Python, Semgrep
también inspeccionó las plantillas HTML/Jinja de ambos sistemas y detectó un
patrón de variable interpolada sin escapar en un atributo `href`
(`mfa_show.html`, presente en ambos sistemas), asociado a CWE-79 (XSS). Se
verificó que el dato en cuestión es una constante fijada por el servidor y
no proviene de entrada de usuario, por lo que no es explotable con el código
actual, pero se recomienda corregirlo por ser un patrón frágil.

Adicionalmente se escribió y probó una regla propia (`no-eval-python`) que
prohíbe el uso de `eval()` en Python, severidad alta, con metadata de CWE-95.
La regla se validó primero contra un archivo de prueba (detectó el patrón
correctamente) y luego contra el código real de ambos sistemas, confirmando
que ninguno usa `eval()`. Se recomienda integrar Semgrep al pipeline de CI
como complemento de Bandit, no como reemplazo.

## 2. Marco normativo y regulatorio aplicable

- Norma de Seguridad de la Información y Ciberseguridad del BCU (SF.SEG.08).
- Recopilación de Normas de Regulación y Control del Sistema Financiero (RNRCSF).
- Marco de Ciberseguridad de AGESIC — dominio GA (control de calidad de código / SAST avanzado).
- Ley N.° 18.331 de Protección de Datos Personales (LPDP).

## 3. Alcance y metodología

- **Alcance:** código fuente de `sistema-turnos/app` y `sistema-facturacion/app` (`../Clase especial 24-8/`), incluyendo Python y plantillas HTML/Jinja.
- **Método:** análisis estático de código (SAST) con reglas públicas y una regla propia.
- **Herramientas:** Semgrep 1.174.0 (`p/security-audit`, 86 reglas, 70 archivos analizados); comparación contra los resultados previos de Bandit.
- **Periodo de ejecución:** 2026-08-26.

## 4. Hallazgos y comparación con Bandit

| ID | Sistema | Herramienta | CWE | Severidad | Descripción | Evidencia |
|---|---|---|---|---|---|---|
| SG-01 | sistema-turnos | Semgrep (`p/security-audit`) | CWE-79 (XSS) | Media (no explotable con el dato actual) | `{{ volver }}` interpolado sin escapar en `href` de `mfa_show.html:8`; el valor es una constante del servidor (`/mfa/verify` o `/mfa/setup`), no input de usuario | `evidencias/EVI-2026-08-26-01-semgrep-audit.md` |
| SG-02 | sistema-facturacion | Semgrep (`p/security-audit`) | CWE-79 (XSS) | Media (no explotable con el dato actual) | Mismo patrón que SG-01, mismo template compartido | idem |

**Comparación con Bandit (VULN-001, `informe-vulnerabilidades.md` de
`Clase especial 24-8/seguridad/`):** Bandit no detectó SG-01/SG-02 porque
solo analiza el árbol de sintaxis de Python, no plantillas HTML. A la
inversa, el ruleset de Semgrep usado (`p/security-audit`) no incluyó una
regla equivalente a `B311` de Bandit para `random.uniform` (VULN-001), que
sigue vigente y sin cambios de estado. Detalle completo del análisis y de la
comparación en [`evidencias/EVI-2026-08-26-04-comparacion.md`](evidencias/EVI-2026-08-26-04-comparacion.md).

## 5. Regla propia: código, prueba y utilidad

Regla `reglas/no-eval.yaml` (id `no-eval-python`, severidad `ERROR`,
metadata CWE-95 / OWASP A03:2021 - Injection). Prohíbe cualquier llamada a
`eval(...)` en código Python.

**Prueba:**
1. Contra `reglas/prueba_eval.py` (archivo de prueba creado para esta
   actividad) → 1 hallazgo, confirma que la regla detecta el patrón.
2. Contra el código real de ambos sistemas → 0 hallazgos, confirma que no
   hay uso de `eval()` en producción y que la regla no genera falsos
   positivos sobre el código actual.

Evidencia: [`evidencias/EVI-2026-08-26-02-regla-no-eval.yaml`](evidencias/EVI-2026-08-26-02-regla-no-eval.yaml), [`evidencias/EVI-2026-08-26-03-semgrep-regla.md`](evidencias/EVI-2026-08-26-03-semgrep-regla.md).

**Utilidad:** una regla propia como esta convierte una prohibición que hoy
depende de que un revisor humano la recuerde en un control automático y
bloqueante en CI. Sirve además como plantilla para reglas específicas del
banco (ver 3 ejemplos propuestos en la evidencia de comparación, sección 3):
prohibición de logging de datos sensibles, prohibición de SQL armado por
concatenación, y exigencia de decorators internos de autorización en
endpoints de negocio.

## 6. Recomendación de integración al desarrollo

Incorporar a CI, como paso adicional a Bandit (no en reemplazo):

```bash
semgrep --config p/security-audit app/
semgrep --config reglas/no-eval.yaml app/ --error   # bloqueante
```

Mantener `reglas/` versionada junto al código, con una regla por archivo y
revisión del equipo de seguridad antes de mergear reglas nuevas. Priorizar
como próxima incorporación las tres reglas propuestas en la sección 3 de
[`evidencias/EVI-2026-08-26-04-comparacion.md`](evidencias/EVI-2026-08-26-04-comparacion.md), en particular la que exige el decorator de autorización en endpoints
`/api/v1/`, por reforzar directamente el control de Step-up MFA (V-01) ya
documentado en `../Clase especial 24-8/informe.md`.

## 7. Riesgos identificados y plan de tratamiento

| ID | Riesgo | Probabilidad | Impacto | Nivel | Tratamiento |
|---|---|---|---|---|---|
| SG-01/SG-02 | Patrón de variable sin escapar en `href` de `mfa_show.html` (CWE-79) | Baja (el valor actual es una constante del servidor) | Medio (si se reutiliza la plantilla con input externo, se vuelve XSS real) | Bajo | En plan — reemplazar `{{ volver }}` interpolado en `href` por rutas fijas o `url_for()` en el próximo sprint |

## 8. Conclusión

Semgrep demostró cubrir una superficie (plantillas HTML/Jinja) que Bandit
estructuralmente no puede analizar, y la capacidad de escribir reglas
propias permite codificar convenciones de seguridad específicas de la
institución como control automático de CI. Se recomienda adoptar Semgrep
como capa adicional — no sustituta — de Bandit en el pipeline de ambos
sistemas.

- **Firma del RSI:** ___________________________
- **Fecha:** ___________________________
