from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

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


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True)
    turno_id_externo = Column(Integer, nullable=False, unique=True)
    paciente = Column(String(128), nullable=False)
    medico = Column(String(128), nullable=False)
    fecha_turno = Column(DateTime, nullable=False)
    monto = Column(Float, nullable=False, default=0.0)
    estado = Column(String(32), nullable=False, default="emitida")
    creado_en = Column(DateTime, default=utcnow)


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
