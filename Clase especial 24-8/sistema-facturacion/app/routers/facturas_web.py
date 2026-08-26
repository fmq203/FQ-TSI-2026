import random
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.audit import log_event
from app.database import get_db
from app.deps import get_current_user
from app.integrations.turnos_client import fetch_turnos_completados
from app.models import Factura, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, msg: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_event(db, actor=user.username, action="read", entity="factura", entity_id=None, detail={"view": "dashboard"})
    facturas = db.query(Factura).order_by(Factura.creado_en.desc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "facturas": facturas, "msg": msg})


@router.post("/facturas/sincronizar")
def sincronizar(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        turnos = fetch_turnos_completados()
    except httpx.HTTPError as exc:
        log_event(db, actor=user.username, action="sync_failed", entity="factura", entity_id=None, detail={"error": str(exc)})
        return RedirectResponse(f"/?msg=Error al contactar Sistema de Turnos: {exc}", status_code=303)

    existentes = {f.turno_id_externo for f in db.query(Factura.turno_id_externo).all()}
    creadas = 0
    for t in turnos:
        if t["id"] in existentes:
            continue
        factura = Factura(
            turno_id_externo=t["id"],
            paciente=t["paciente"],
            medico=t["medico"],
            fecha_turno=datetime.fromisoformat(t["fecha"]),
            monto=round(random.uniform(3000, 8000), 2),
        )
        db.add(factura)
        db.commit()
        db.refresh(factura)
        log_event(db, actor=user.username, action="create", entity="factura", entity_id=factura.id,
                   detail={"turno_id_externo": t["id"], "monto": factura.monto})
        creadas += 1

    log_event(db, actor=user.username, action="sync_ok", entity="factura", entity_id=None,
               detail={"turnos_recibidos": len(turnos), "facturas_creadas": creadas})
    return RedirectResponse(f"/?msg=Sincronizado: {creadas} factura(s) nueva(s) de {len(turnos)} turno(s)", status_code=303)
