# apps/api/schemas/campaigns.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CampaignCreate(BaseModel):
    channel: str = "email"
    template_id: int
    segment_id: int

class CampaignOut(BaseModel):
    id: int
    channel: str
    template_id: int
    segment_id: int
    status: str
    launched_at: Optional[datetime] = None

    class Config:
        from_attributes = True