# apps/api/schemas/email_preview.py
from pydantic import BaseModel


class EmailPreviewRequest(BaseModel):
    template_id: int
    recipient: str = "demo@example.com"
    fake_uid: str = "preview-uid-001"
    campaign_id: int = 999
    target_id: int = 999