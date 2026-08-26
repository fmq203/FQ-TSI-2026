# Sistema de Facturación (Sistema B)

Web UI + backend en Python (FastAPI). Sistema completamente independiente de Turnos: DB propia (`facturacion.db`), usuarios propios, autenticación propia. Se integra con Sistema de Turnos únicamente vía su REST API.

## Requisitos cubiertos
- **Login + MFA**: igual que Sistema A, usuario/contraseña + TOTP, enrolamiento obligatorio en el primer login.
- **Interacción entre sistemas**: botón "Sincronizar" en el dashboard llama a `app/integrations/turnos_client.py`, que obtiene turnos completados desde la API de Sistema de Turnos y genera facturas.
- **Autenticación de API con MFA (saliente)**: para llamar a Sistema de Turnos, este sistema calcula un código TOTP vigente (`current_totp_code`) a partir de un secreto compartido y lo envía junto al `client_secret` — dos factores, no solo una API key estática.
- **Log inmutable**: `audit_log` propio, con la misma cadena de hashes que Sistema A.
- **Auditoría de acceso a BD**: toda lectura/escritura de `facturas`, sincronizaciones y autenticaciones quedan registradas.

## Cómo correr
```bash
cd sistema-facturacion
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Antes de arrancar, completar en `.env` las variables `TURNOS_CLIENT_SECRET` y `TURNOS_CLIENT_TOTP_SECRET` que Sistema de Turnos imprime en su consola la primera vez que arranca (ver README de `sistema-turnos`).

```bash
uvicorn app.main:app --reload --port 8002
```

Abrir `http://localhost:8002/login`, ingresar con el admin, configurar MFA. Con Sistema de Turnos corriendo en el puerto 8001 y turnos marcados como "completado", usar el botón **Sincronizar** para generar facturas.
