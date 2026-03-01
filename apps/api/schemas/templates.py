# apps/api/schemas/templates.py
from pydantic import BaseModel
from typing import Any, Dict, Optional

class TemplateCreate(BaseModel):
    channel: str = "email"
    name: str
    html_body: str
    signals: Optional[Dict[str, Any]] = None
    version: int = 1

class TemplateOut(TemplateCreate):
    id: int
    class Config:
        from_attributes = True