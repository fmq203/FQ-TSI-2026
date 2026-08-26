# Informe Ejecutivo — Actividad 08: Escaneo de Seguridad Web con OWASP ZAP

**Institución:** Banco Ficticio del Uruguay (ejercicio académico)
**Responsable de Seguridad de la Información (RSI):** [Nombre y cargo]
**Destinatario:** Banco Central del Uruguay — Superintendencia de Instituciones Financieras
**Asunto:** Análisis dinámico (DAST) con OWASP ZAP sobre la API de la Actividad 4
**Fecha:** 2026-08-26 | **Versión:** 1.0 | **Clasificación:** Confidencial

## 1. Resumen ejecutivo

Se ejecutó OWASP ZAP (Zed Attack Proxy, versión estable oficial) en modo
headless contra la API REST desarrollada en la Actividad 4
(`04/app.py`), aplicando spider y active scan (~140 reglas de ataque:
inyección SQL, XSS, SSRF, XXE, path traversal, command injection, entre
otras). El resultado fue **0 hallazgos de severidad Alta o Media, y 2 de
severidad Baja**, ambos mapeados a la categoría A05:2021 (Security
Misconfiguration) del OWASP Top 10. El hallazgo de mayor relevancia —
exposición de la versión del servidor vía el header `Server` — es
significativo no por su severidad técnica, sino porque **el código
intenta explícitamente corregirlo y no lo logra en el entorno de
ejecución actual**, evidenciando el valor de complementar el análisis
estático (Actividad 07, Bandit/Semgrep) con análisis dinámico. Se dejó un
plan de remediación priorizado con ambos hallazgos y sus responsables.

## 2. Marco normativo y regulatorio aplicable

- Norma de Seguridad de la Información y Ciberseguridad del BCU (SF.SEG.08).
- Recopilación de Normas de Regulación y Control del Sistema Financiero (RNRCSF).
- Marco de Ciberseguridad de AGESIC — evaluación de riesgos GR.2.
- OWASP Top 10 (2021) como taxonomía de referencia.

## 3. Alcance y metodología

- **Alcance:** API REST de la Actividad 4 (`04/app.py`), endpoints `GET /health` (público) y `GET /usuarios` (protegido con Bearer token), corriendo en `localhost:5000`.
- **Método:** DAST (Dynamic Application Security Testing) — spider + active scan con OWASP ZAP contra la aplicación en ejecución.
- **Herramientas:** OWASP ZAP estable (`ghcr.io/zaproxy/zaproxy:stable`, Docker, headless). Autenticación inyectada vía el add-on Replacer de ZAP (header `Authorization: Bearer <API_TOKEN>` en cada petición).
- **Periodo de ejecución:** 2026-08-26.

## 4. Descripción de la actividad y nota metodológica

Al ser la API un servicio JSON puro sin páginas HTML, el spider
tradicional de ZAP (que sigue enlaces `<a href>`) no encontró rutas para
rastrear al apuntarlo a la raíz del sitio. Se resolvió apuntando el active
scan directamente a cada endpoint conocido por el código
(`/health`, `/usuarios?id=1`), lo cual permitió que las ~140 reglas de
ataque se ejecutaran efectivamente contra ambos. Esta limitación del
spider clásico frente a APIs sin frontend queda documentada como
aprendizaje de la actividad.

## 5. Hallazgos por severidad y categoría OWASP

| ID | Hallazgo | Severidad (Confianza) | CWE | OWASP Top 10 | Endpoint(s) |
|---|---|---|---|---|---|
| DAST-01 | Exposición de versión de servidor vía header `Server: Werkzeug/3.1.8 Python/3.12.3` | Low (High) | CWE-497 | A05:2021 — Security Misconfiguration | Todos |
| DAST-02 | Header `Cross-Origin-Resource-Policy` ausente | Low (Medium) | CWE-693 | A05:2021 — Security Misconfiguration | `/health` |
| DAST-03 | CORS Header (informativo — configuración verificada como correcta) | Informational | — | — | `/usuarios` |
| DAST-04 | Non-Storable / Storable Content (informativo — comportamiento de caché correcto) | Informational | CWE-524 | — | Todos |

**Totales:** 0 Alto, 0 Medio, 2 Bajo, 2 Informativo. Reportes completos de
ZAP (HTML/JSON) y análisis por hallazgo en `evidencias/`.

## 6. Comparación SAST vs DAST

| | SAST (Actividad 07 — Bandit/Semgrep) | DAST (Actividad 08 — ZAP) |
|---|---|---|
| Qué analiza | El código fuente, sin ejecutarlo | La aplicación real, en ejecución |
| Sobre esta API | No se corrió SAST específico sobre `04/app.py` en esta sesión, pero por lectura de código el `pop("Server", ...)` parecería una mitigación correcta | Confirma que el header **sigue presente en cada respuesta real** |
| Por qué difieren | El análisis estático no puede saber que el servidor de desarrollo Werkzeug reinyecta el header `Server` a nivel de socket, después de que el código de la aplicación ya devolvió su `Response` | El DAST manda peticiones HTTP reales y observa la respuesta final tal como la recibiría un atacante — incluyendo lo que agregan capas por debajo del código de la aplicación |
| Conclusión | Ninguna de las dos cubre el 100% de la superficie por sí sola. Este caso concreto es evidencia directa de por qué la normativa exige ambas capas de prueba antes de producción. | |

## 7. Plan de remediación priorizado

| Prioridad | ID | Acción correctiva | Responsable | Plazo |
|---|---|---|---|---|
| 1 | DAST-01 | Migrar de `app.run()` (servidor de desarrollo) a gunicorn/uWSGI detrás de nginx, con `proxy_hide_header Server;` / `server_tokens off;` | Equipo de desarrollo / DevOps | Antes de cualquier despliegue a producción |
| 2 | DAST-02 | Agregar `Cross-Origin-Resource-Policy: same-origin` en `set_security_headers()` (`04/app.py:57`) | Equipo de desarrollo | Próximo sprint |
| — | DAST-03, DAST-04 | Sin acción — configuración/comportamiento ya correctos | — | Aceptado |

Detalle completo, con justificación de cada prioridad, en
[`evidencias/EVI-2026-08-26-04-remediacion.md`](evidencias/EVI-2026-08-26-04-remediacion.md).

## 8. Riesgos identificados y evaluación

| ID Riesgo | Descripción | Probabilidad | Impacto | Nivel | Tratamiento |
|---|---|---|---|---|---|
| R-01 | Exposición de versión exacta de framework/runtime (`Server` header) facilita a un atacante buscar CVEs específicas antes de intentar explotarlas | Media (información pública en cada respuesta) | Bajo (no es una vulnerabilidad en sí, es reconocimiento) | Bajo | En plan — remediación DAST-01 |
| R-02 | Ausencia de `Cross-Origin-Resource-Policy` en `/health` habilita incrustación cross-origin del recurso | Baja | Bajo (endpoint sin datos sensibles) | Bajo | En plan — remediación DAST-02 |

## 9. Indicadores y métricas de la actividad

- Reglas activas ejecutadas por objetivo: ~140.
- Objetivos escaneados: 3 (raíz, `/usuarios?id=1` autenticado, `/health`).
- Hallazgos: 0 altos, 0 medios, 2 bajos, 2 informativos.
- Hallazgos con plan de remediación: 2/2 (100% de los accionables).
- Cobertura: 2/2 endpoints de la API (100%).

## 10. Conclusión

La API de la Actividad 4 mostró una postura de seguridad sólida frente al
escaneo dinámico: ninguna de las ~140 reglas de ataque activo (inyección,
XSS, SSRF, etc.) encontró una vulnerabilidad explotable, resultado
consistente con la validación estricta de parámetros y las cabeceras de
seguridad ya presentes en el código. El único hallazgo relevante —el leak
del header `Server`— no es una falla de diseño del código de la
aplicación sino una limitación del servidor de desarrollo usado para
correrla, y queda con plan de remediación claro antes de cualquier
despliegue productivo. El ejercicio confirma el valor de ejecutar DAST
como complemento obligatorio del SAST, no como sustituto.

- **Firma del RSI:** ___________________________
- **Fecha:** ___________________________
