# channels/email/providers/smtp_provider.py
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from core.config.settings import settings


def send_email_smtp(
    to_email: str,
    subject: str,
    html_content: str,
    plain_text: str | None = None,
) -> dict:
    """
    Sends an email using SMTP configuration from settings.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    if plain_text is None:
        plain_text = (
            "Este correo forma parte de una simulación académica controlada. "
            "Si estás viendo este mensaje en texto plano, abre la versión HTML."
        )

    msg.set_content(plain_text)
    msg.add_alternative(html_content, subtype="html")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)

    return {
        "ok": True,
        "to": to_email,
        "subject": subject,
        "mode": "smtp",
    }