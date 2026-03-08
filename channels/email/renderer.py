# channels/email/renderer.py
from __future__ import annotations

from pathlib import Path
from jinja2 import Template as JinjaTemplate

from core.config.settings import settings


def render_email_template(
    html_body: str,
    uid: str,
    recipient: str,
    campaign_id: int,
    target_id: int,
    template_id: int,
) -> str:
    """
    Renderiza la plantilla HTML final para un target específico.
    """

    tracking_dot = f"{settings.tracker_base_url}/open.gif?uid={uid}"
    landing_url = f"{settings.tracker_base_url}/r?uid={uid}"

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
    )
    return rendered


def write_outbox_html(
    campaign_id: int,
    target_id: int,
    html_content: str,
) -> str:
    """
    Guarda el HTML renderizado en data/outbox/ para abrirlo manualmente.
    Devuelve la ruta absoluta del archivo creado.
    """
    outbox_dir = Path(settings.outbox_dir)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    file_path = outbox_dir / f"campaign_{campaign_id}_target_{target_id}.html"
    file_path.write_text(html_content, encoding="utf-8")
    return str(file_path.resolve())