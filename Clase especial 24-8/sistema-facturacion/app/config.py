import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./facturacion.db")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CambiarEsta123!")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    PENDING_MFA_EXPIRE_MINUTES = 5
    ISSUER_NAME = "SistemaFacturacion"

    TURNOS_API_URL = os.environ.get("TURNOS_API_URL", "http://localhost:8001")
    TURNOS_CLIENT_ID = os.environ.get("TURNOS_CLIENT_ID", "sistema-facturacion")
    TURNOS_CLIENT_SECRET = os.environ.get("TURNOS_CLIENT_SECRET", "")
    TURNOS_CLIENT_TOTP_SECRET = os.environ.get("TURNOS_CLIENT_TOTP_SECRET", "")


settings = Settings()
