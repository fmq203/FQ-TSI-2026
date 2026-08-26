from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.audit import log_event
from app.database import get_db
from app.deps import get_current_user
from app.models import Turno, User
from app.security import verify_totp

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_event(db, actor=user.username, action="read", entity="turno", entity_id=None, detail={"view": "dashboard"})
    turnos = db.query(Turno).order_by(Turno.fecha.asc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "turnos": turnos})


@router.post("/turnos/nuevo")
def crear_turno(
    paciente: str = Form(...),
    documento_paciente: str = Form(...),
    medico: str = Form(...),
    fecha: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    turno = Turno(
        paciente=paciente,
        documento_paciente=documento_paciente,
        medico=medico,
        fecha=datetime.fromisoformat(fecha),
        creado_por=user.username,
    )
    db.add(turno)
    db.commit()
    db.refresh(turno)
    log_event(db, actor=user.username, action="create", entity="turno", entity_id=turno.id,
               detail={"paciente": paciente, "medico": medico, "fecha": fecha})
    return RedirectResponse("/", status_code=303)


@router.post("/turnos/{turno_id}/completar")
def completar_turno(
    turno_id: int,
    mfa_code: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_totp(user.mfa_secret, mfa_code):
        log_event(db, actor=user.username, action="step_up_mfa_failed", entity="turno", entity_id=turno_id)
        raise HTTPException(401, "Codigo MFA invalido para confirmar la accion")
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado")
    turno.estado = "completado"
    db.commit()
    log_event(db, actor=user.username, action="update_estado", entity="turno", entity_id=turno_id,
               detail={"estado": "completado"})
    return RedirectResponse("/", status_code=303)
