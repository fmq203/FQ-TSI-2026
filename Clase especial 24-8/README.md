# Clase especial 2 - Seguridad

Dos sistemas independientes que interactúan por REST, con Step-up MFA, auditoría inmutable, DLP, SBOM y gestión de vulnerabilidades basada en riesgo — alineado con la actividad "Arquitectura Distribuida Segura, Step-up MFA, SBOM, RBVM y Acceso Privilegiado a BD" (ver [Actividad RSI - Mfa,sbomb.pdf](Actividad%20RSI%20-%20Mfa,sbomb.pdf)).

## Arquitectura

```
┌─────────────────────────┐         REST (JWT + TOTP)        ┌──────────────────────────────┐
│   Sistema de Turnos (A) │ <──────────────────────────────  │  Sistema de Facturación (B)  │
│   Python / FastAPI      │   GET  /api/v1/turnos             │   Python / FastAPI            │
│   Web UI + REST API     │   GET  /api/v1/pacientes (DLP)    │   Web UI                      │
│   DB: turnos.db (propia)│   POST /api/v1/auth/token          │   DB: facturacion.db (propia) │
│   :8001                 │   POST /api/v1/turnos/{id}/completar (step-up X-MFA-Code)          │
└─────────────────────────┘                                   └──────────────────────────────┘
        │                                                               │
        └── login humano + MFA (TOTP) ──────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌──────────────────┐        ┌──────────────────────┐
│  seguridad/    │         │  sbom/            │        │  caso-directivo-pam.md│
│  SAST+SCA+DAST │         │  CycloneDX x2      │        │  Bastion/PAM + RBAC   │
│  + db_roles.sql│         │                    │        │  para acceso directivo│
└───────────────┘         └──────────────────┘        └──────────────────────┘
```

Cada sistema tiene su propia base de datos, sus propios usuarios y su propio esquema de auditoría — son independientes; la única conexión entre ambos es la API REST de Turnos, que Facturación consume para generar comprobantes de los turnos completados.

## Checklist de la consigna del curso

| Requisito | Dónde está |
|---|---|
| Dos sistemas comunicados vía REST, uno en Python | Ambos en Python/FastAPI: [sistema-turnos](sistema-turnos/) y [sistema-facturacion](sistema-facturacion/) |
| Enrolamiento y validación MFA TOTP (Google Authenticator) en login | `routers/auth_web.py` en ambos sistemas, QR vía `qrcode` + `pyotp` |
| Step-up MFA en endpoint crítico (header `X-MFA-Code`) | `POST /api/v1/turnos/{id}/completar` — `app/deps.py::require_api_step_up_mfa` (401 sin header/código inválido, 200 con TOTP fresco) |
| Autenticación de API entre sistemas | `POST /api/v1/auth/token`: `client_secret` + TOTP (dos factores) → Bearer de corta duración |
| SBOM formato CycloneDX | [sbom/](sbom/) — `sbom-sistema-turnos.json`, `sbom-sistema-facturacion.json`, generados con `cyclonedx-py` |
| Log inmutable con hash-chaining | `app/audit.py` en ambos sistemas — SHA-256 encadenado, verificable en `/admin/audit` |
| Middleware DLP contra exfiltración de PII | `GET /api/v1/pacientes` + `app/dlp.py` (Sistema de Turnos): bloquea 403 si hay >5 registros sin paginar o documento sin enmascarar |
| RBAC / roles de BD (aplicativo vs. auditor) | [seguridad/db_roles.sql](seguridad/db_roles.sql) — diseño para Postgres (SQLite no soporta GRANT) |
| Gestión de vulnerabilidades basada en riesgo (CWE/CVE/CVSS) | [informe.md](informe.md) sección 3 (matriz RBVM) + [seguridad/](seguridad/) (SAST/SCA/DAST) |
| Caso de uso Bastion/PAM (acceso directivo a BD) | [caso-directivo-pam.md](caso-directivo-pam.md) |
| Bitácora RSI | [bitacora.md](bitacora.md) |
| Informe ejecutivo (Anexo A) | [informe.md](informe.md) |
| Evidencias | [evidencias/](evidencias/) (ver su README: algunas requieren captura manual tuya) |

## Cómo correr todo

1. **Sistema de Turnos** (ver [sistema-turnos/README.md](sistema-turnos/README.md)):
   ```bash
   cd sistema-turnos
   python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload --port 8001
   ```
   Copiar del log de arranque las credenciales de API impresas (`TURNOS_CLIENT_SECRET`, `TURNOS_CLIENT_TOTP_SECRET`).

2. **Sistema de Facturación** (ver [sistema-facturacion/README.md](sistema-facturacion/README.md)):
   ```bash
   cd sistema-facturacion
   python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   cp .env.example .env   # pegar ahí las credenciales del paso anterior
   uvicorn app.main:app --reload --port 8002
   ```

3. En Sistema A (`:8001/login`): loguearse, configurar MFA, crear un turno (con documento del paciente) y marcarlo "completado" desde la web (pide código MFA).

4. En Sistema B (`:8002/login`): loguearse, configurar MFA, tocar "Sincronizar" para traer el turno completado como factura.

5. Revisar `/admin/audit` en ambos sistemas para ver el log inmutable de todo lo anterior.

6. Probar el step-up MFA y el DLP directamente sobre la API (ver `evidencias/EVI-2026-08-24-02-stepup-transcript.txt` y `EVI-2026-08-24-04-dlp-blocked-transcript.txt` para el detalle exacto de los `curl`).

7. SBOM: `bash sbom/run_sbom.sh` (requiere los `venv` de cada sistema ya creados).

8. Gestión de vulnerabilidades: ver [seguridad/README.md](seguridad/README.md).

9. Informe ejecutivo y caso del directivo: [informe.md](informe.md), [caso-directivo-pam.md](caso-directivo-pam.md), [bitacora.md](bitacora.md).
