from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.audit import log_event
from app.config import settings
from app.database import get_db
from app.deps import get_current_api_client, require_api_step_up_mfa
from app.models import ApiClient, Turno
from app.security import create_jwt, verify_password, verify_totp

router = APIRouter(prefix="/api/v1")


def _mask_documento(documento: str) -> str:
    if not documento:
        return documento
    if len(documento) <= 4:
        return "*" * len(documento)
    return documento[:2] + "*" * (len(documento) - 4) + documento[-2:]


@router.post("/auth/token")
def issue_api_token(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    totp_code: str = Form(...),
    db: Session = Depends(get_db),
):
    """Autenticacion de API con dos factores: secreto estatico del cliente + codigo TOTP rotativo."""
    client = db.query(ApiClient).filter(ApiClient.client_id == client_id, ApiClient.activo == True).first()  # noqa: E712
    if not client or not verify_password(client_secret, client.client_secret_hash):
        log_event(db, actor=f"api:{client_id}", action="api_auth_failed", entity="api_client", entity_id=client_id,
                   detail={"reason": "credenciales"})
        raise HTTPException(401, "Credenciales de API invalidas")
    if not verify_totp(client.totp_secret, totp_code):
        log_event(db, actor=f"api:{client_id}", action="api_auth_failed", entity="api_client", entity_id=client_id,
                   detail={"reason": "totp"})
        raise HTTPException(401, "Codigo TOTP invalido")

    token = create_jwt(client.client_id, {"purpose": "api"}, settings.API_TOKEN_EXPIRE_MINUTES)
    log_event(db, actor=f"api:{client_id}", action="api_auth_ok", entity="api_client", entity_id=client_id)
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.API_TOKEN_EXPIRE_MINUTES * 60}


@router.get("/turnos")
def listar_turnos(
    estado: str | None = None,
    client: ApiClient = Depends(get_current_api_client),
    db: Session = Depends(get_db),
):
    query = db.query(Turno)
    if estado:
        query = query.filter(Turno.estado == estado)
    turnos = query.order_by(Turno.fecha.asc()).all()
    log_event(db, actor=f"api:{client.client_id}", action="read", entity="turno", entity_id=None,
               detail={"estado_filtro": estado, "cantidad": len(turnos)})
    return [
        {
            "id": t.id,
            "paciente": t.paciente,
            "medico": t.medico,
            "fecha": t.fecha.isoformat(),
            "estado": t.estado,
        }
        for t in turnos
    ]


@router.post("/turnos/{turno_id}/completar")
def completar_turno_api(
    turno_id: int,
    client: ApiClient = Depends(require_api_step_up_mfa),
    db: Session = Depends(get_db),
):
    """Endpoint critico: requiere Bearer token (API-Key) + header X-MFA-Code fresco
    (step-up), equivalente al /api/v1/transferencia de la consigna. Sin el header,
    o con un codigo invalido, responde 401 y no ejecuta el cambio."""
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado")
    turno.estado = "completado"
    db.commit()
    log_event(db, actor=f"api:{client.client_id}", action="step_up_update_estado", entity="turno", entity_id=turno_id,
               detail={"estado": "completado", "via": "api_step_up_mfa"})
    return {"id": turno.id, "estado": turno.estado}


@router.get("/pacientes")
def listar_pacientes(
    page: int = 1,
    page_size: int = 5,
    raw: bool = False,
    client: ApiClient = Depends(get_current_api_client),
    db: Session = Depends(get_db),
):
    """Expone datos personales (paciente + documento) protegidos por la politica DLP
    del middleware en main.py: paginado <=5 registros y documento enmascarado por
    defecto. El parametro `raw` existe solo para poder demostrar/evidenciar que el
    middleware bloquea la fuga si algun consumidor intenta saltarse los controles."""
    query = db.query(Turno).order_by(Turno.id.asc())
    total = query.count()
    if raw:
        turnos = query.all()
    else:
        page_size = min(max(page_size, 1), 5)
        turnos = query.offset((max(page, 1) - 1) * page_size).limit(page_size).all()

    registros = [
        {
            "id": t.id,
            "paciente": t.paciente,
            "documento": t.documento_paciente if raw else _mask_documento(t.documento_paciente),
        }
        for t in turnos
    ]
    log_event(db, actor=f"api:{client.client_id}", action="read", entity="paciente", entity_id=None,
               detail={"cantidad": len(registros), "raw": raw})
    return {"total": total, "page": page, "page_size": page_size, "registros": registros}
