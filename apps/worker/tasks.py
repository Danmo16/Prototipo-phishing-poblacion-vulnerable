# apps/worker/tasks.py
from __future__ import annotations

from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from apps.worker.celery_app import celery_app
from core.db.session import SessionLocal
from core.domain.models import Campaign, Target, Template, Event

@celery_app.task(name="worker.simulate_send_campaign")
def simulate_send_campaign(campaign_id: int) -> dict:
    """
    Simula el envío de una campaña:
    - genera un uid por target
    - registra evento 'delivered' (simulado)
    - NO envía email real (para mantenerlo académico/seguro)
    """
    db: Session = SessionLocal()
    try:
        camp = db.query(Campaign).get(campaign_id)
        if not camp:
            return {"ok": False, "error": "Campaign not found"}

        tpl = db.query(Template).get(camp.template_id)
        if not tpl:
            return {"ok": False, "error": "Template not found"}

        # targets del segmento (MVP: todos los targets con segment_id)
        targets = db.query(Target).filter(Target.segment_id == camp.segment_id).all()
        sent = 0

        for t in targets:
            uid = str(uuid.uuid4())
            ev = Event(
                campaign_id=camp.id,
                target_id=t.id,
                template_id=tpl.id,
                event_type="delivered",
                occurred_at=datetime.utcnow(),
                meta={"uid": uid, "mode": "simulated_outbox"},
            )
            db.add(ev)
            sent += 1

        camp.status = "launched"
        camp.launched_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "campaign_id": camp.id, "targets": sent}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()