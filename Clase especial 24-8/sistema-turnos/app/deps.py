from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiClient, User
from app.security import decode_jwt, verify_totp


class NotAuthenticated(HTTPException):
    """Sesion web ausente/invalida: se maneja distinto de un 401 comun para poder
    redirigir a /login en vez de mostrar JSON crudo (ver main.py)."""

    def __init__(self, detail: str):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


def get_current_user(session: str | None = Cookie(default=None, alias="turnos_session"), db: Session = Depends(get_db)) -> User:
    if not session:
        raise NotAuthenticated("No autenticado")
    try:
        payload = decode_jwt(session)
    except Exception:
        raise NotAuthenticated("Sesion invalida o expirada")
    if payload.get("purpose") != "session":
        raise NotAuthenticated("Sesion invalida")
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user:
        raise NotAuthenticated("Usuario no encontrado")
    return user


def require_step_up_mfa(x_mfa_code: str | None = Header(default=None), user: User = Depends(get_current_user)) -> User:
    if not x_mfa_code or not verify_totp(user.mfa_secret, x_mfa_code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Codigo MFA requerido o invalido para esta accion")
    return user


def get_current_api_client(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> ApiClient:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de API requerido")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_jwt(token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de API invalido o expirado")
    if payload.get("purpose") != "api":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de proposito incorrecto")
    client = db.query(ApiClient).filter(ApiClient.client_id == payload["sub"], ApiClient.activo == True).first()  # noqa: E712
    if not client:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Cliente de API no encontrado o inactivo")
    return client


def require_api_step_up_mfa(
    x_mfa_code: str | None = Header(default=None), client: ApiClient = Depends(get_current_api_client)
) -> ApiClient:
    """Step-up MFA para endpoints criticos de la API: el bearer token (API-Key) alcanza
    para lectura, pero una accion critica exige ademas un codigo TOTP fresco por header,
    revalidado en cada llamada (no basta con haberlo usado al emitir el token)."""
    if not x_mfa_code or not verify_totp(client.totp_secret, x_mfa_code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Header X-MFA-Code requerido o invalido para esta accion")
    return client
