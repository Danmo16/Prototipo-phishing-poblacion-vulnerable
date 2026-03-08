# apps/api/routes/campaigns.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from apps.api.schemas.campaigns import CampaignCreate, CampaignOut
from apps.worker.tasks import simulate_send_campaign
from core.domain.models import Campaign, Template, Segment

router = APIRouter()


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    tpl = db.query(Template).get(payload.template_id)
    seg = db.query(Segment).get(payload.segment_id)

    if not tpl:
        raise HTTPException(status_code=400, detail="template_id does not exist")

    if not seg:
        raise HTTPException(status_code=400, detail="segment_id does not exist")

    camp = Campaign(
        channel=payload.channel,
        template_id=payload.template_id,
        segment_id=payload.segment_id,
        status="draft",
        launched_at=None,
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)
    return camp


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.id.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    camp = db.query(Campaign).get(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return camp


@router.post("/{campaign_id}/launch")
def launch_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Lanza una campaña en modo simulado:
    - verifica que exista
    - dispara la tarea Celery
    - devuelve el task_id para trazabilidad
    """
    camp = db.query(Campaign).get(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if camp.status == "launched":
        raise HTTPException(status_code=400, detail="Campaign is already launched")

    job = simulate_send_campaign.delay(campaign_id)

    return {
        "ok": True,
        "message": "Campaign launch task queued",
        "campaign_id": campaign_id,
        "task_id": job.id,
    }