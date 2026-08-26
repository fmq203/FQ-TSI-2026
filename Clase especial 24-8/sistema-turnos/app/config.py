import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./turnos.db")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CambiarEsta123!")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    API_TOKEN_EXPIRE_MINUTES = 5
    PENDING_MFA_EXPIRE_MINUTES = 5
    ISSUER_NAME = "SistemaTurnos"


settings = Settings()
