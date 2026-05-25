# apps/api/routes/targets.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db, get_current_active_user, get_current_admin_user
from apps.api.schemas.targets import TargetCreate, TargetOut
from core.domain.models import Segment, Target, User

router = APIRouter()


@router.post("", response_model=TargetOut)
def create_target(
    payload: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    segment = db.query(Segment).get(payload.segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    target = Target(**payload.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("", response_model=list[TargetOut])
def list_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return db.query(Target).order_by(Target.id.desc()).all()


@router.get("/{target_id}", response_model=TargetOut)
def get_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    target = db.query(Target).get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target