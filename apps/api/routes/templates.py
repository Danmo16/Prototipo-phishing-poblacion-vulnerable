# apps/api/routes/templates.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from apps.api.schemas.templates import TemplateCreate, TemplateOut
from core.domain.models import Template

router = APIRouter()

@router.post("", response_model=TemplateOut)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    tpl = Template(**payload.model_dump())
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl

@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(Template).order_by(Template.id.desc()).all()

@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(Template).get(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl