from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from apps.api.schemas.targets import TargetCreate, TargetOut
from core.domain.models import Target, Segment

router = APIRouter()

@router.post("", response_model=TargetOut)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    seg = db.query(Segment).get(payload.segment_id)
    if not seg:
        raise HTTPException(status_code=400, detail="segment_id does not exist")

    t = Target(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.get("", response_model=list[TargetOut])
def list_targets(db: Session = Depends(get_db)):
    return db.query(Target).order_by(Target.id.desc()).all()

@router.get("/{target_id}", response_model=TargetOut)
def get_target(target_id: int, db: Session = Depends(get_db)):
    t = db.query(Target).get(target_id)
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    return t