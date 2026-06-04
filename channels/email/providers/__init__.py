# channels/email/providers/__init__.py
from channels.email.providers.smtp_provider import send_email_smtp

__all__ = ["send_email_smtp"]