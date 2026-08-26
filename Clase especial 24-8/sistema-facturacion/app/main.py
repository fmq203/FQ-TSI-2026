from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.deps import NotAuthenticated
from app.models import User
from app.routers import admin, auth_web, facturas_web
from app.security import hash_password, new_totp_secret

app = FastAPI(title="Sistema de Facturacion")

app.include_router(auth_web.router)
app.include_router(facturas_web.router)
app.include_router(admin.router)


@app.exception_handler(NotAuthenticated)
def redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.on_event("startup")
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == settings.ADMIN_USERNAME).first():
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                mfa_secret=new_totp_secret(),
                mfa_enabled=False,
            )
            db.add(admin_user)
            db.commit()
            print(f"[seed] Usuario admin creado: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
            print("[seed] Debera configurar MFA en el primer login.")
        if not settings.TURNOS_CLIENT_SECRET:
            print("[seed] AVISO: falta TURNOS_CLIENT_SECRET/TURNOS_CLIENT_TOTP_SECRET en .env")
            print("[seed] Copialos desde la consola de Sistema de Turnos al arrancarlo por primera vez.")
    finally:
        db.close()
