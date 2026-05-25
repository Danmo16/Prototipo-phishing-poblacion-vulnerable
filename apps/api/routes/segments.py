# apps/api/routes/segments.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.deps import get_db, get_current_active_user, get_current_admin_user
from apps.api.schemas.segments import SegmentCreate, SegmentOut
from core.domain.models import Segment, User

router = APIRouter()


@router.post("", response_model=SegmentOut)
def create_segment(
    payload: SegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    segment = Segment(**payload.model_dump())
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


@router.get("", response_model=list[SegmentOut])
def list_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return db.query(Segment).order_by(Segment.id.desc()).all()