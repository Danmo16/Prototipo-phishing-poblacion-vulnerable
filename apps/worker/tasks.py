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
from channels.email.providers import send_email_smtp
from core.config.settings import settings
from core.db.session import SessionLocal
from core.domain.models import Campaign, Target, Template, Event


@celery_app.task(name="worker.simulate_send_campaign")
def simulate_send_campaign(campaign_id: int) -> dict:
    """
    Procesa una campaña en dos modos posibles:
    - simulated_outbox: genera archivos HTML/TXT en data/outbox
    - smtp: envía el correo realmente por SMTP

    En ambos casos registra evento 'delivered' si el procesamiento fue exitoso.
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
        deliveries: list[dict] = []

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

            delivery_meta = {
                "uid": target.uid,
                "subject": rendered_subject,
                "delivery_mode": settings.delivery_mode,
            }

            if settings.delivery_mode == "smtp":
                smtp_result = send_email_smtp(
                    to_email=target.recipient,
                    subject=rendered_subject,
                    html_content=rendered_html,
                )
                delivery_meta["smtp_result"] = smtp_result
                deliveries.append(
                    {
                        "target_id": target.id,
                        "recipient": target.recipient,
                        "mode": "smtp",
                        "subject": rendered_subject,
                    }
                )

            else:
                outbox_info = write_outbox_email(
                    campaign_id=camp.id,
                    target_id=target.id,
                    recipient=target.recipient,
                    subject=rendered_subject,
                    html_content=rendered_html,
                )
                delivery_meta["html_file"] = outbox_info["html_file"]
                delivery_meta["meta_file"] = outbox_info["meta_file"]
                deliveries.append(
                    {
                        "target_id": target.id,
                        "recipient": target.recipient,
                        "mode": "simulated_outbox",
                        "subject": rendered_subject,
                        "html_file": outbox_info["html_file"],
                        "meta_file": outbox_info["meta_file"],
                    }
                )

            ev = Event(
                campaign_id=camp.id,
                target_id=target.id,
                template_id=tpl.id,
                event_type="delivered",
                occurred_at=datetime.utcnow(),
                meta=delivery_meta,
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
            "delivery_mode": settings.delivery_mode,
            "deliveries": deliveries,
        }

    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

    finally:
        db.close()