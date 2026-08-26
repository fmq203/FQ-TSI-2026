from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    # Naive UTC a proposito: SQLite descarta el tzinfo al persistir, y el
    # hash-chain de auditoria necesita que created_at sea identico al
    # escribir y al releer, o la verificacion de integridad da falso positivo.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="operador")
    mfa_secret = Column(String(64), nullable=False)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utcnow)


class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True)
    paciente = Column(String(128), nullable=False)
    documento_paciente = Column(String(32), nullable=False, default="")
    medico = Column(String(128), nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(String(32), nullable=False, default="pendiente")
    creado_por = Column(String(64), nullable=False)
    creado_en = Column(DateTime, default=utcnow)


class ApiClient(Base):
    __tablename__ = "api_clients"

    id = Column(Integer, primary_key=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(128), nullable=False)
    totp_secret = Column(String(64), nullable=False)
    descripcion = Column(String(128), nullable=False, default="")
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)
    actor = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    entity = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=True)
    detail = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=utcnow)
