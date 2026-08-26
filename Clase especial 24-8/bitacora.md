# Bitácora RSI — Actividad Arquitectura Distribuida Segura

## Diagrama de flujo de autenticación

### Login con MFA (humano, ambos sistemas)

```
Usuario → POST /login (usuario+contraseña)
        → si es válido: cookie "pending" (5 min) → redirect a /mfa/setup (1ra vez) o /mfa/verify
        → usuario ingresa código TOTP de 6 dígitos (Google Authenticator / Authy)
        → servidor valida con pyotp.TOTP(secret).verify(code)
        → si es válido: cookie de sesión (JWT, 30 min) → acceso al dashboard
        → si es inválido: rechazo, sin sesión emitida
```

### Step-up MFA en endpoint crítico (API)

```
Cliente (Sistema de Facturación) → POST /api/v1/auth/token (client_id + client_secret + totp_code)
                                  → recibe Bearer token de corta duración (5 min)

Acción crítica → POST /api/v1/turnos/{id}/completar
               Header: Authorization: Bearer <token>
               Header: X-MFA-Code: <código TOTP fresco>
               → sin X-MFA-Code o código inválido: 401
               → con X-MFA-Code válido: 200, cambia estado + registra auditoría
```

El Bearer token (obtenido una vez) NO alcanza por sí solo para la acción crítica: el código TOTP se revalida en cada llamada al endpoint sensible (`app/deps.py::require_api_step_up_mfa`), no solo al emitir el token.

## Comprobación de integridad de la cadena criptográfica de auditoría

Mecanismo (`app/audit.py`): cada entrada de `audit_log` almacena `prev_hash` (hash de la entrada anterior) y `entry_hash = SHA256(prev_hash | actor | accion | entidad | entity_id | detalle | timestamp)`. La primera entrada encadena contra un hash génesis (`"0"*64`).

`verify_chain()` recorre la tabla en orden y recalcula cada hash; si algún valor no coincide, reporta el `id` de la primera entrada comprometida. Verificado en `/admin/audit` de ambos sistemas: estado **OK** (cadena íntegra) tras el flujo completo de login, creación/completado de turnos, sincronización de facturas, y los bloqueos DLP.

Dos bugs reales encontrados y corregidos durante el desarrollo (documentados en el historial de la sesión):
1. Pérdida de zona horaria al persistir `created_at` en SQLite rompía la verificación (falso positivo de manipulación). Corregido normalizando a UTC naive de forma consistente.
2. Inconsistencia entre `"None"` (hash) y `""` (valor almacenado) para `entity_id` nulo, mismo efecto. Corregido unificando la representación antes de hashear y de persistir.

## SBOM generado

- `sbom/sbom-sistema-turnos.json` — 61 componentes (directos + transitivos), formato CycloneDX.
- `sbom/sbom-sistema-facturacion.json` — 65 componentes, formato CycloneDX.
- Generados con `cyclonedx-py environment -o <archivo>` sobre el entorno virtual de cada sistema (`sbom/run_sbom.sh`).
- Cruce contra vulnerabilidades conocidas con `pip-audit` (`seguridad/run_sca.sh`) — resultado y hallazgos priorizados en `informe.md`, sección 3 (V-03, V-05).

## Análisis y resolución del caso de acceso directivo a base de datos

Ver documento dedicado: [`caso-directivo-pam.md`](caso-directivo-pam.md). Resumen del dictamen: acceso directo denegado; exigido tránsito por Bastion Host/PAM con MFA, rol de solo lectura sobre vistas con Data Masking, y auditoría inmutable de cada sentencia ejecutada. Incluye el SQL de referencia para roles y vista enmascarada (`seguridad/db_roles.sql`).
