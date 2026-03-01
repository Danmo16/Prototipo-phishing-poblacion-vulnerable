from pydantic import BaseModel
from typing import Any, Dict, Optional

class TargetCreate(BaseModel):
    segment_id: int
    recipient: str
    meta: Optional[Dict[str, Any]] = None

class TargetOut(TargetCreate):
    id: int

    class Config:
        from_attributes = True