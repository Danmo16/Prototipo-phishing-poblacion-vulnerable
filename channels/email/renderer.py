# channels/email/renderer.py
from __future__ import annotations

from pathlib import Path
from jinja2 import Template as JinjaTemplate

from core.config.settings import settings


def render_email_subject(subject: str | None, recipient: str, uid: str) -> str:
    subject = subject or "Simulación académica"
    template = JinjaTemplate(subject)
    return template.render(
        recipient=recipient,
        name=recipient,
        uid=uid,
    )


def render_email_template(
    html_body: str,
    uid: str,
    recipient: str,
    campaign_id: int,
    target_id: int,
    template_id: int,
) -> str:
    tracking_dot = f"{settings.tracker_base_url}/open.gif?uid={uid}"
    landing_url = f"{settings.tracker_base_url}/r?uid={uid}"
    report_url = f"{settings.tracker_base_url}/report?uid={uid}"

    template = JinjaTemplate(html_body)

    rendered = template.render(
        uid=uid,
        recipient=recipient,
        name=recipient,
        campaign_id=campaign_id,
        target_id=target_id,
        template_id=template_id,
        tracking_dot=tracking_dot,
        landing_url=landing_url,
        report_url=report_url,
    )
    return rendered


def write_outbox_email(
    campaign_id: int,
    target_id: int,
    recipient: str,
    subject: str,
    html_content: str,
) -> dict[str, str]:
    outbox_dir = Path(settings.outbox_dir)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    html_path = outbox_dir / f"campaign_{campaign_id}_target_{target_id}.html"
    meta_path = outbox_dir / f"campaign_{campaign_id}_target_{target_id}.txt"

    html_path.write_text(html_content, encoding="utf-8")

    meta_text = (
        f"campaign_id: {campaign_id}\n"
        f"target_id: {target_id}\n"
        f"recipient: {recipient}\n"
        f"subject: {subject}\n"
        f"delivery_mode: simulated_outbox\n"
        f"html_file: {html_path.name}\n"
    )
    meta_path.write_text(meta_text, encoding="utf-8")

    return {
        "html_file": str(html_path.resolve()),
        "meta_file": str(meta_path.resolve()),
    }