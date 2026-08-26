from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.deps import NotAuthenticated
from app.dlp import register_dlp_middleware
from app.models import ApiClient, User
from app.routers import admin, api_v1, auth_web, turnos_web
from app.security import hash_password, new_client_secret, new_totp_secret

app = FastAPI(title="Sistema de Turnos")

app.include_router(auth_web.router)
app.include_router(turnos_web.router)
app.include_router(api_v1.router)
app.include_router(admin.router)
register_dlp_middleware(app)


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

        if not db.query(ApiClient).filter(ApiClient.client_id == "sistema-facturacion").first():
            secret = new_client_secret()
            totp_secret = new_totp_secret()
            client = ApiClient(
                client_id="sistema-facturacion",
                client_secret_hash=hash_password(secret),
                totp_secret=totp_secret,
                descripcion="Credenciales para que Sistema de Facturacion consuma esta API",
            )
            db.add(client)
            db.commit()
            print("=" * 70)
            print("[seed] Credenciales de API para Sistema de Facturacion (copiar a su .env):")
            print(f"  TURNOS_CLIENT_ID=sistema-facturacion")
            print(f"  TURNOS_CLIENT_SECRET={secret}")
            print(f"  TURNOS_CLIENT_TOTP_SECRET={totp_secret}")
            print("=" * 70)
    finally:
        db.close()
