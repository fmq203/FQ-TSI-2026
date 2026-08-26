import hashlib
import json

from sqlalchemy.orm import Session

from app.models import AuditLog

GENESIS_HASH = "0" * 64


def _compute_hash(prev_hash: str, actor: str, action: str, entity: str, entity_id: str, detail: str, created_at) -> str:
    payload = f"{prev_hash}|{actor}|{action}|{entity}|{entity_id}|{detail}|{created_at.isoformat()}"
    return hashlib.sha256(payload.encode()).hexdigest()


def log_event(db: Session, actor: str, action: str, entity: str, entity_id, detail: dict | None = None) -> AuditLog:
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last.entry_hash if last else GENESIS_HASH
    detail_str = json.dumps(detail or {}, default=str, sort_keys=True)
    from app.models import utcnow

    created_at = utcnow()
    entity_id_str = str(entity_id) if entity_id is not None else ""
    entry_hash = _compute_hash(prev_hash, actor, action, entity, entity_id_str, detail_str, created_at)

    entry = AuditLog(
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        actor=actor,
        action=action,
        entity=entity,
        entity_id=entity_id_str,
        detail=detail_str,
        created_at=created_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> tuple[bool, int | None]:
    prev_hash = GENESIS_HASH
    for entry in db.query(AuditLog).order_by(AuditLog.id.asc()).all():
        expected = _compute_hash(
            prev_hash, entry.actor, entry.action, entry.entity, entry.entity_id or "", entry.detail, entry.created_at
        )
        if expected != entry.entry_hash or entry.prev_hash != prev_hash:
            return False, entry.id
        prev_hash = entry.entry_hash
    return True, None
