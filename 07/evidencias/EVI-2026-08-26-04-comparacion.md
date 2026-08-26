# EVI-2026-08-26-04 — Análisis comparativo Bandit vs Semgrep (asistido por IA)

> Nota: la consigna pide una captura de pantalla (`.png`). Esta sesión no tiene
> forma de generar una imagen de pantalla real, así que esta evidencia queda
> como documento de texto con el análisis pedido en el Paso 2/3 de la
> actividad ("pide a la IA que explique los hallazgos y los relacione con
> CWE" / "compara qué detecta Semgrep y no Bandit").

## 1. Interpretación de los hallazgos de Semgrep (`p/security-audit`)

Semgrep reportó **2 hallazgos**, ambos de la misma regla
`generic.html-templates.security.var-in-href.var-in-href`, uno en cada
sistema (`sistema-turnos/app/templates/mfa_show.html:8` y
`sistema-facturacion/app/templates/mfa_show.html:8`):

```html
<a href="{{ volver }}"><button type="button">Volver a ingresar el código</button></a>
```

- **CWE relacionado:** CWE-79 (Cross-Site Scripting). El patrón general que
  busca la regla es una variable de plantilla insertada sin escapar dentro de
  un atributo `href`; si esa variable llegara a contener `javascript:...`, el
  navegador la ejecutaría al hacer clic.
- **Análisis de explotabilidad real:** se rastreó el origen de `volver` en
  `app/routers/auth_web.py:115` en ambos sistemas:
  ```python
  volver = "/mfa/verify" if user.mfa_enabled else "/mfa/setup"
  ```
  El valor es una constante fijada por el servidor (una de dos rutas
  internas), **no** proviene de un parámetro de request, cookie ni input de
  usuario. Semgrep no tiene alcance para seguir el dato desde la ruta hasta
  la plantilla (no hace taint tracking entre `.py` y `.html` con esta regla),
  así que marca el patrón sintáctico sin poder confirmar la fuente.
- **Veredicto:** falso positivo de riesgo real / verdadero positivo de
  patrón inseguro. No es explotable con el código actual, pero es el tipo de
  código fragil que se vuelve una XSS real en cuanto alguien reutilice esa
  misma plantilla pasando un valor derivado de un query param (`?volver=`)
  sin revisar este detalle. Recomendación: usar `url_for()` o directamente
  cambiar a rutas fijas (`{% if user.mfa_enabled %}/mfa/verify{% else %}...{% endif %}`)
  para eliminar la variable interpolada del atributo `href`.

## 2. Comparación Bandit vs Semgrep

| | Bandit | Semgrep (`p/security-audit`) |
|---|---|---|
| Hallazgos en `sistema-turnos` | 0 | 1 (XSS en `mfa_show.html`) |
| Hallazgos en `sistema-facturacion` | 1 (`random.uniform`, CWE-330, Low) | 1 (XSS en `mfa_show.html`) |
| Alcance de archivos | Solo `.py` (AST de Python) | Multi-lenguaje: `.py` **y** `.html`/Jinja en este caso |
| Regla que detectó `random.uniform` (CWE-330) | Sí (`B311`) | No aparece en `p/security-audit` para este caso |
| Regla que detectó la XSS de plantilla (CWE-79) | No puede — no analiza HTML | Sí |

**Conclusión de la comparación:** las dos herramientas son complementarias,
no redundantes. Bandit está limitado al árbol de sintaxis de Python, por lo
que nunca iba a poder ver un problema que vive en un archivo `.html`. Semgrep
sí cruza esa frontera porque sus reglas `generic.html-templates.*` entienden
plantillas Jinja/Mustache, pero el ruleset `p/security-audit` no incluyó el
patrón `random.uniform` para Python en esta corrida (Bandit lo capturó por
tener una regla específica y directa, `B311`, orientada a ese caso). Ninguna
de las dos detecta el 100% de la superficie por sí sola.

## 3. ¿Por qué un equipo de seguridad debería definir reglas SAST propias? (3 ejemplos para un banco)

Los rulesets públicos (`p/security-audit`, `p/owasp-top-ten`, etc.) cubren
patrones genéricos del lenguaje o del framework, pero no conocen las
convenciones internas de una institución. Una regla propia permite codificar
como control automático de CI algo que hoy solo vive en una guía de estilo o
en la cabeza de un revisor senior. Ejemplos concretos para un banco:

1. **Prohibir logging de datos sensibles**: una regla que detecte
   `logger.info(...)`, `print(...)` o `logging.*` cuando el argumento incluye
   variables con nombres como `password`, `token`, `secret`, `documento`,
   `tarjeta`, `cvv` — evita fugas de PII/credenciales en logs que luego
   terminan en un SIEM o en texto plano (relevante para LPDP / Ley 18.331).
2. **Prohibir queries SQL armadas con f-strings o `.format()`** en vez de
   parámetros bindeados (`cursor.execute(f"SELECT ... {id}")`) — refuerza el
   control de SQL injection (CWE-89) más allá de lo que detecta un ruleset
   genérico, porque puede adaptarse a los helpers de DB propios del banco
   (ORM interno, wrapper de conexión, etc.).
3. **Exigir el uso del decorator interno de autorización** en cada endpoint
   nuevo bajo `/api/v1/` (por ejemplo, exigir `@require_api_step_up_mfa` o
   equivalente en cualquier función `async def` decorada con
   `@router.post(...)` que toque una tabla de negocio) — esto es exactamente
   el tipo de control que un ruleset público jamás podría conocer, porque
   depende de una convención interna, y es el que directamente refuerza el
   hallazgo V-01 (Step-up MFA) ya documentado en
   `../Clase especial 24-8/informe.md`.

Esta última es la más valiosa: convierte un control de seguridad que hoy se
verifica manualmente en cada revisión de código en un gate automático de CI
que no depende de que el revisor se acuerde de chequearlo.
