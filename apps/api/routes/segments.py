# apps/api/routes/segments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from apps.api.schemas.segments import SegmentCreate, SegmentOut
from core.domain.models import Segment

router = APIRouter()

@router.post("", response_model=SegmentOut)
def create_segment(payload: SegmentCreate, db: Session = Depends(get_db)):
    seg = Segment(**payload.model_dump())
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg

@router.get("", response_model=list[SegmentOut])
def list_segments(db: Session = Depends(get_db)):
    return db.query(Segment).order_by(Segment.id.desc()).all()

@router.get("/{segment_id}", response_model=SegmentOut)
def get_segment(segment_id: int, db: Session = Depends(get_db)):
    seg = db.query(Segment).get(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    return seg