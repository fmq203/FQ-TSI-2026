# Sistema de Turnos (Sistema A)

Web UI + REST API en Python (FastAPI). Fuente de verdad de turnos médicos. Sistema completamente independiente de Facturación: DB propia, usuarios propios, autenticación propia.

## Requisitos cubiertos
- **Login + MFA**: usuario/contraseña + TOTP (Google Authenticator/Authy). Primer login fuerza enrolamiento MFA.
- **MFA de step-up**: completar un turno exige reingresar el código TOTP vigente (no alcanza con la sesión activa).
- **Autenticación de API con MFA**: Sistema B obtiene un token llamando a `/api/v1/auth/token` con `client_id` + `client_secret` (factor estático) + `totp_code` (factor rotativo, código TOTP de 30s) — dos factores, igual que un login humano.
- **Log inmutable**: `audit_log` con hash encadenado (`prev_hash` + datos → `entry_hash`, sha256). No existen endpoints de edición/borrado sobre esa tabla. Verificación de integridad en `/admin/audit`.
- **Auditoría de acceso a BD**: toda lectura/escritura de `turnos` y toda autenticación queda registrada con actor, acción, entidad y timestamp.
- **Step-up MFA en endpoint crítico de la API**: `POST /api/v1/turnos/{id}/completar` exige el Bearer token *y además* un header `X-MFA-Code` con TOTP fresco, revalidado en cada llamada (no alcanza con el token ya emitido). Ver `app/deps.py::require_api_step_up_mfa`.
- **DLP (Data Loss Prevention)**: `GET /api/v1/pacientes` expone PII (paciente + documento). Un middleware (`app/dlp.py`) inspecciona la respuesta y la bloquea con `403` si supera 5 registros sin paginar o si el documento no está enmascarado — con evento crítico registrado en la auditoría inmutable.

## Cómo correr
```bash
cd sistema-turnos
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

Al arrancar por primera vez, la consola imprime:
- Usuario admin y contraseña inicial (definidos en `.env`).
- Credenciales de API (`client_id`, `client_secret`, `totp_secret`) que hay que copiar al `.env` de `sistema-facturacion`.

Abrir `http://localhost:8001/login`, ingresar con el admin, configurar MFA escaneando el QR.

## Endpoints principales
- `GET/POST /login`, `/mfa/setup`, `/mfa/verify`, `/logout`
- `GET /` dashboard de turnos, `POST /turnos/nuevo` (incluye documento del paciente), `POST /turnos/{id}/completar` (requiere `mfa_code`, formulario web)
- `POST /api/v1/auth/token` (form: `client_id`, `client_secret`, `totp_code`)
- `GET /api/v1/turnos?estado=completado` (header `Authorization: Bearer <token>`)
- `POST /api/v1/turnos/{id}/completar` — **endpoint crítico**: `Authorization: Bearer <token>` + `X-MFA-Code: <totp>` (401 si falta o es inválido)
- `GET /api/v1/pacientes?page=1&page_size=5` — paginado, documento enmascarado por defecto. `?raw=true` existe solo para demostrar que el middleware DLP bloquea el intento (403) — no usar en producción.
- `GET /admin/audit` visor del log inmutable + verificación de cadena de hashes
