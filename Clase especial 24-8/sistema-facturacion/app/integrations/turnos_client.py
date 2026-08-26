import httpx

from app.config import settings
from app.security import current_totp_code


def get_api_token() -> str:
    """Obtiene un token de corta duracion contra Sistema de Turnos usando dos factores:
    client_secret (estatico) + codigo TOTP vigente (rotativo)."""
    totp_code = current_totp_code(settings.TURNOS_CLIENT_TOTP_SECRET)
    resp = httpx.post(
        f"{settings.TURNOS_API_URL}/api/v1/auth/token",
        data={
            "client_id": settings.TURNOS_CLIENT_ID,
            "client_secret": settings.TURNOS_CLIENT_SECRET,
            "totp_code": totp_code,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_turnos_completados() -> list[dict]:
    token = get_api_token()
    resp = httpx.get(
        f"{settings.TURNOS_API_URL}/api/v1/turnos",
        params={"estado": "completado"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
