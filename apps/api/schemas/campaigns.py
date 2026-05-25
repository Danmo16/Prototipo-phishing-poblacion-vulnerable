# apps/api/schemas/campaigns.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CampaignCreate(BaseModel):
    channel: str = "email"
    template_id: int
    segment_id: int


class CampaignOut(CampaignCreate):
    id: int
    launched_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class CampaignLaunchOut(BaseModel):
    ok: bool
    message: str
    campaign_id: int
    task_id: str