# Informe Ejecutivo — Evaluación de Controles de Seguridad

**Institución:** Banco Ficticio del Uruguay (ejercicio académico)
**Responsable de Seguridad de la Información (RSI):** [Nombre y cargo]
**Destinatario:** Banco Central del Uruguay — Superintendencia de Instituciones Financieras
**Asunto:** Evaluación de Controles de Acceso Escalonado (Step-up MFA), Trazabilidad Inmutable, SBOM, DLP y Control de Accesos Privilegiados a BD
**Fecha:** 2026-08-24 | **Versión:** 1.0 | **Clasificación:** Confidencial

## 1. Resumen ejecutivo

Se desplegaron y evaluaron dos plataformas independientes — **Sistema de Turnos** (Frontend/Gateway con base de datos propia) y **Sistema de Facturación** (consumidor vía REST) — que interoperan mediante una API autenticada con dos factores (secreto de cliente + TOTP rotativo). Se verificó: autenticación fuerte TOTP compatible con Google Authenticator en el login humano de ambos sistemas; Step-up MFA por header `X-MFA-Code` en el endpoint crítico `POST /api/v1/turnos/{id}/completar`; un middleware DLP que bloquea con HTTP 403 cualquier intento de extracción masiva o exposición de PII en texto claro desde `GET /api/v1/pacientes`; una pista de auditoría inmutable con encadenamiento criptográfico SHA-256 verificable en ambos sistemas; y un inventario de dependencias (SBOM) en formato CycloneDX que permitió identificar componentes con CVEs publicadas. Se dictaminó además sobre el caso de acceso directo de un directivo a la base de datos, exigiendo arquitectura Bastion/PAM con enmascaramiento de datos (ver `caso-directivo-pam.md`).

No se identificaron hallazgos críticos sin mitigación. Los riesgos residuales (dependencias con CVE publicada, ausencia de Bastion/PAM real desplegado) están documentados con plan de tratamiento en la sección 3.

## 2. Marco normativo y estándares aplicables

- Norma de Ciberseguridad del BCU (SF.SEG.08) y Marco de Ciberseguridad de AGESIC.
- Ley N.° 18.331 de Protección de Datos Personales (LPDP) y Acción de Habeas Data.
- Estándares: OWASP CycloneDX (SBOM), RFC 6238 (TOTP), taxonomías CWE, CVE y CVSS. NIST SP 800-218 (SSDF) como marco de referencia de ciclo de vida seguro.

## 3. Matriz de Gestión de Vulnerabilidades Basada en Riesgo (RBVM)

| ID | Activo / Componente | CWE / CVE | CVSS Base | Exposición / Contexto | Nivel de Riesgo Real | Plan de Tratamiento |
|---|---|---|---|---|---|---|
| V-01 | Endpoint `POST /api/v1/turnos/{id}/completar` (Sistema de Turnos) | CWE-306 (Autenticación ausente para función crítica) / N/A | 8.8 (Alto) | Endpoint transaccional entre sistemas, cambia estado de negocio | **Crítico** (sin mitigación) → **Bajo** (mitigado) | Mitigado con Step-up MFA: exige Bearer token + header `X-MFA-Code` revalidado en cada llamada (`app/deps.py::require_api_step_up_mfa`). Verificado: 401 sin header, 200 con TOTP válido. |
| V-02 | Acceso administrativo a Base de Datos Core | CWE-284 (Control de acceso inadecuado) / N/A | 7.5 (Alto) | Acceso directo de operadores/directivos vía cliente SQL, fuera de la aplicación | **Alto** (sin mitigación) → **Medio** (mitigado, control documentado no desplegado) | Diseño de RBAC con roles `rol_aplicativo` (SELECT/INSERT, sin acceso a `audit_log`) y `rol_auditor` (solo lectura de auditoría) en `seguridad/db_roles.sql`; caso del directivo resuelto con Bastion/PAM + vistas con Data Masking en `caso-directivo-pam.md`. Pendiente: despliegue real de Bastion (Teleport/StrongDM) fuera de alcance de este entregable. |
| V-03 | Dependencia `python-multipart` 0.0.9 (usada por ambos sistemas para parsear formularios de login) | CWE-400 (Consumo de recursos no controlado) / **CVE-2024-53981** | 7.5 (Alto) | Dependencia directa, expuesta en todo endpoint que recibe `multipart/form-data` (login, formularios web) | Medio (requiere payload malicioso específico, no hay evidencia de explotación activa) | Actualizar a `python-multipart>=0.0.18` en `requirements.txt` de ambos sistemas. Programado para el próximo ciclo de mantenimiento. |
| V-04 | Endpoint `GET /api/v1/pacientes` (Sistema de Turnos) | CWE-200 (Exposición de información sensible) / N/A | 7.5 (Alto) | Expone nombre + documento de identidad de pacientes (PII bajo LPDP) | **Alto** (sin mitigación) → **Bajo** (mitigado) | Mitigado con middleware DLP (`app/dlp.py`): bloquea con 403 si la respuesta supera 5 registros sin paginar o expone el documento sin enmascarar. Enmascaramiento por defecto (`_mask_documento`) + límite de página server-side. Verificado con evidencia (ver sección 4 y `evidencias/`). |
| V-05 | Dependencia `starlette` 0.38.6 (framework base de FastAPI, ambos sistemas) | CWE-400 (Consumo de recursos no controlado) / **CVE-2024-47874** | 7.5 (Alto) | Dependencia transitiva de todo el tráfico HTTP de ambos sistemas | Bajo (aceptado transitoriamente, sin vector activo conocido en el entorno de desarrollo) | Programado: actualizar `fastapi`/`starlette` a versión que incluya el parche en el próximo sprint de mantenimiento de dependencias. |

*Metodología RBVM: Riesgo = Impacto al Negocio × Probabilidad de Explotación, ajustado por exposición real del componente (interno vs. expuesto a internet, dato sensible vs. no sensible), no solo por el CVSS Base intrínseco.*

Fuente de los hallazgos V-03 y V-05: `pip-audit` sobre `requirements.txt` de ambos sistemas (`seguridad/run_sca.sh`, salida en `seguridad/sca/`). Fuente V-01, V-02, V-04: análisis de arquitectura sobre el código de `sistema-turnos/app/`.

## 4. Evidencia técnica de los controles implementados

- **Step-up MFA (V-01):** `POST /api/v1/turnos/{id}/completar` sin `X-MFA-Code` → `401`; con código TOTP válido → `200`. Ver `evidencias/EVI-2026-08-24-02-stepup-block-ok.png` (o el registro de comandos si se documentó por CLI).
- **Auditoría inmutable:** cadena de hashes SHA-256 verificada sin roturas en `/admin/audit` de ambos sistemas (`app/audit.py::verify_chain`).
- **DLP (V-04):** `GET /api/v1/pacientes?raw=true` bloqueado con `403` y evento `dlp_blocked` registrado en la auditoría inmutable, tanto por "más de 5 registros sin paginar" como por "documento en texto claro".
- **SBOM:** `sbom/sbom-sistema-turnos.json` y `sbom/sbom-sistema-facturacion.json`, formato CycloneDX 1.x, generados con `cyclonedx-py environment`.

## 5. Dictamen técnico sobre acceso directo de directivos a bases de datos

No se autoriza el acceso directo con credenciales de aplicación. Todo acceso de un directivo a la base de producción debe transitar por un Bastion Host / PAM Gateway con MFA obligatorio, usar un rol de solo lectura sobre vistas con Data Masking (documento de identidad parcialmente enmascarado), y quedar registrado en la tabla de auditoría inmutable con encadenamiento criptográfico. Desarrollo completo del caso, arquitectura y SQL de referencia en `caso-directivo-pam.md`.

## 6. Conclusiones y firmas

Los controles de autenticación escalonada, auditoría inmutable y prevención de fuga de datos se encuentran implementados y verificados sobre el código desplegado. Los riesgos residuales identificados (V-03, V-05) corresponden a dependencias de terceros con parche disponible, sin evidencia de explotación en el entorno evaluado, y quedan con plan de tratamiento y responsable asignado.

- **Firma del RSI:** ___________________________
- **Fecha:** ___________________________
