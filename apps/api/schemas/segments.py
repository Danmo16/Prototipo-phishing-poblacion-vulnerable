# apps/api/schemas/segments.py
from pydantic import BaseModel
from typing import Optional

class SegmentCreate(BaseModel):
    age_bracket: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None

class SegmentOut(SegmentCreate):
    id: int
    class Config:
        from_attributes = True