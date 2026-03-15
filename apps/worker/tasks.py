# apps/worker/tasks.py
from __future__ import annotations

from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from apps.worker.celery_app import celery_app
from channels.email.renderer import (
    render_email_subject,
    render_email_template,
    write_outbox_email,
)
from channels.email.validators import validate_email_template
from core.db.session import SessionLocal
from core.domain.models import Campaign, Target, Template, Event


@celery_app.task(name="worker.simulate_send_campaign")
def simulate_send_campaign(campaign_id: int) -> dict:
    """
    Simula el envío de una campaña:
    - genera uid por target si no existe
    - renderiza subject y HTML final
    - guarda HTML y metadatos en data/outbox/
    - registra evento 'delivered'
    """
    db: Session = SessionLocal()

    try:
        camp = db.query(Campaign).get(campaign_id)
        if not camp:
            return {"ok": False, "error": "Campaign not found"}

        tpl = db.query(Template).get(camp.template_id)
        if not tpl:
            return {"ok": False, "error": "Template not found"}

        validation = validate_email_template(
            html_body=tpl.html_body,
            subject=tpl.subject,
        )
        if not validation["valid"]:
            return {
                "ok": False,
                "error": "Template validation failed",
                "validation_errors": validation["errors"],
            }

        targets = db.query(Target).filter(Target.segment_id == camp.segment_id).all()
        sent = 0
        outbox_files: list[dict[str, str]] = []

        for target in targets:
            if not target.uid:
                target.uid = str(uuid.uuid4())
                db.add(target)
                db.flush()

            rendered_subject = render_email_subject(
                subject=tpl.subject,
                recipient=target.recipient,
                uid=target.uid,
            )

            rendered_html = render_email_template(
                html_body=tpl.html_body,
                uid=target.uid,
                recipient=target.recipient,
                campaign_id=camp.id,
                target_id=target.id,
                template_id=tpl.id,
            )

            outbox_info = write_outbox_email(
                campaign_id=camp.id,
                target_id=target.id,
                recipient=target.recipient,
                subject=rendered_subject,
                html_content=rendered_html,
            )
            outbox_files.append(outbox_info)

            ev = Event(
                campaign_id=camp.id,
                target_id=target.id,
                template_id=tpl.id,
                event_type="delivered",
                occurred_at=datetime.utcnow(),
                meta={
                    "uid": target.uid,
                    "mode": "simulated_outbox",
                    "subject": rendered_subject,
                    "html_file": outbox_info["html_file"],
                    "meta_file": outbox_info["meta_file"],
                },
            )
            db.add(ev)
            sent += 1

        camp.status = "launched"
        camp.launched_at = datetime.utcnow()
        db.add(camp)
        db.commit()

        return {
            "ok": True,
            "campaign_id": camp.id,
            "targets": sent,
            "outbox_files": outbox_files,
        }

    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

    finally:
        db.close()