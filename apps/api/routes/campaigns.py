# apps/api/routes/campaigns.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.deps import get_db, get_current_active_user, get_current_admin_user
from apps.api.schemas.campaigns import CampaignCreate, CampaignOut, CampaignLaunchOut
from apps.worker.tasks import simulate_send_campaign
from core.domain.models import Campaign, Segment, Template, User

router = APIRouter()


@router.post("", response_model=CampaignOut)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    template = db.query(Template).get(payload.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    segment = db.query(Segment).get(payload.segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return db.query(Campaign).order_by(Campaign.id.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/launch", response_model=CampaignLaunchOut)
def launch_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == "launched":
        raise HTTPException(status_code=400, detail="Campaign is already launched")

    task = simulate_send_campaign.delay(campaign_id)

    return CampaignLaunchOut(
        ok=True,
        message="Campaign launch task queued",
        campaign_id=campaign_id,
        task_id=task.id,
    )