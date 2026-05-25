# apps/api/routes/email_tools.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db, get_current_active_user
from apps.api.schemas.email_preview import EmailPreviewRequest
from channels.email.renderer import render_email_subject, render_email_template
from channels.email.validators import validate_email_template
from core.domain.models import Template, User

router = APIRouter()


@router.post("/preview")
def preview_email(
    payload: EmailPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tpl = db.query(Template).get(payload.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    validation = validate_email_template(
        html_body=tpl.html_body,
        subject=tpl.subject,
    )
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Template validation failed",
                "errors": validation["errors"],
            },
        )

    subject = render_email_subject(
        subject=tpl.subject,
        recipient=payload.recipient,
        uid=payload.fake_uid,
    )

    html = render_email_template(
        html_body=tpl.html_body,
        uid=payload.fake_uid,
        recipient=payload.recipient,
        campaign_id=payload.campaign_id,
        target_id=payload.target_id,
        template_id=tpl.id,
    )

    return {
        "template_id": tpl.id,
        "template_name": tpl.name,
        "subject": subject,
        "html_preview": html,
    }