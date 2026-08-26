import base64
import io

import qrcode
from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.audit import log_event
from app.config import settings
from app.database import get_db
from app.models import User
from app.security import create_jwt, decode_jwt, totp_provisioning_uri, verify_password, verify_totp

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _pending_user(pending: str | None, db: Session) -> User | None:
    if not pending:
        return None
    try:
        payload = decode_jwt(pending)
    except Exception:
        return None
    if payload.get("purpose") != "mfa_pending":
        return None
    return db.query(User).filter(User.username == payload["sub"]).first()


def _qr_b64(secret: str, username: str) -> str:
    uri = totp_provisioning_uri(secret, username)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        log_event(db, actor=username, action="login_failed", entity="user", entity_id=username)
        return templates.TemplateResponse(
            "login.html", {"request": request, "user": None, "error": "Usuario o contraseña invalidos"}, status_code=401
        )

    log_event(db, actor=user.username, action="login_password_ok", entity="user", entity_id=user.username)
    pending = create_jwt(user.username, {"purpose": "mfa_pending"}, settings.PENDING_MFA_EXPIRE_MINUTES)
    destino = "/mfa/verify" if user.mfa_enabled else "/mfa/setup"
    resp = RedirectResponse(destino, status_code=303)
    resp.set_cookie("facturacion_pending", pending, httponly=True, samesite="lax", max_age=settings.PENDING_MFA_EXPIRE_MINUTES * 60)
    return resp


@router.get("/mfa/setup", response_class=HTMLResponse)
def mfa_setup_form(request: Request, pending: str | None = Cookie(default=None, alias="facturacion_pending"), db: Session = Depends(get_db)):
    user = _pending_user(pending, db)
    if not user or user.mfa_enabled:
        return RedirectResponse("/login", status_code=303)
    qr_b64 = _qr_b64(user.mfa_secret, user.username)
    return templates.TemplateResponse(
        "mfa_setup.html", {"request": request, "user": None, "qr_b64": qr_b64, "secret": user.mfa_secret}
    )


@router.post("/mfa/setup")
def mfa_setup_submit(
    request: Request, code: str = Form(...), pending: str | None = Cookie(default=None, alias="facturacion_pending"), db: Session = Depends(get_db)
):
    user = _pending_user(pending, db)
    if not user or user.mfa_enabled:
        return RedirectResponse("/login", status_code=303)
    if not verify_totp(user.mfa_secret, code):
        log_event(db, actor=user.username, action="mfa_setup_failed", entity="user", entity_id=user.username)
        return templates.TemplateResponse(
            "mfa_setup.html",
            {"request": request, "user": None, "error": "Codigo invalido", "qr_b64": "", "secret": user.mfa_secret},
            status_code=401,
        )
    user.mfa_enabled = True
    db.commit()
    log_event(db, actor=user.username, action="mfa_enabled", entity="user", entity_id=user.username)

    session = create_jwt(user.username, {"purpose": "session", "role": user.role}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("facturacion_pending")
    resp.set_cookie("facturacion_session", session, httponly=True, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return resp


@router.get("/mfa/verify", response_class=HTMLResponse)
def mfa_verify_form(request: Request, pending: str | None = Cookie(default=None, alias="facturacion_pending"), db: Session = Depends(get_db)):
    user = _pending_user(pending, db)
    if not user or not user.mfa_enabled:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("mfa_verify.html", {"request": request, "user": None})


@router.get("/mfa/show", response_class=HTMLResponse)
def mfa_show(request: Request, pending: str | None = Cookie(default=None, alias="facturacion_pending"), db: Session = Depends(get_db)):
    """Vuelve a mostrar el QR/semilla ya existente (no genera un secreto nuevo).
    Requiere haber pasado usuario+contraseña (cookie pending); pensado para cuando
    se perdio el acceso a la app autenticadora y hay que volver a escanear."""
    user = _pending_user(pending, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    qr_b64 = _qr_b64(user.mfa_secret, user.username)
    volver = "/mfa/verify" if user.mfa_enabled else "/mfa/setup"
    return templates.TemplateResponse(
        "mfa_show.html", {"request": request, "user": None, "qr_b64": qr_b64, "secret": user.mfa_secret, "volver": volver}
    )


@router.post("/mfa/verify")
def mfa_verify_submit(
    request: Request, code: str = Form(...), pending: str | None = Cookie(default=None, alias="facturacion_pending"), db: Session = Depends(get_db)
):
    user = _pending_user(pending, db)
    if not user or not user.mfa_enabled:
        return RedirectResponse("/login", status_code=303)
    if not verify_totp(user.mfa_secret, code):
        log_event(db, actor=user.username, action="mfa_verify_failed", entity="user", entity_id=user.username)
        return templates.TemplateResponse(
            "mfa_verify.html", {"request": request, "user": None, "error": "Codigo invalido"}, status_code=401
        )
    log_event(db, actor=user.username, action="login_mfa_ok", entity="user", entity_id=user.username)
    session = create_jwt(user.username, {"purpose": "session", "role": user.role}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("facturacion_pending")
    resp.set_cookie("facturacion_session", session, httponly=True, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("facturacion_session")
    return resp
