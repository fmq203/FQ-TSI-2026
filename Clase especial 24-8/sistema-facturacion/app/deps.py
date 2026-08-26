from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_jwt, verify_totp


class NotAuthenticated(HTTPException):
    """Sesion web ausente/invalida: se maneja distinto de un 401 comun para poder
    redirigir a /login en vez de mostrar JSON crudo (ver main.py)."""

    def __init__(self, detail: str):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


def get_current_user(session: str | None = Cookie(default=None, alias="facturacion_session"), db: Session = Depends(get_db)) -> User:
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
