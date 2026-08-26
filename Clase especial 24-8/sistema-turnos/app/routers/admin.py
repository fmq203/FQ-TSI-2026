from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.audit import verify_chain
from app.database import get_db
from app.deps import get_current_user
from app.models import AuditLog, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/audit", response_class=HTMLResponse)
def audit_view(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entries = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    chain_ok, broken_id = verify_chain(db)
    return templates.TemplateResponse(
        "audit.html",
        {"request": request, "user": user, "entries": entries, "chain_ok": chain_ok, "broken_id": broken_id},
    )
