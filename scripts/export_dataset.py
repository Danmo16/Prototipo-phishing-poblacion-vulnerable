# scripts/export_dataset.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.db.session import SessionLocal
from core.domain.models import Campaign, Event, Segment, Target, Template


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def extract_signal(signals: dict | None, key: str) -> int:
    if not signals:
        return 0
    value = signals.get(key, 0)
    return 1 if value in [1, True, "1", "true", "True"] else 0


def build_dataset(db: Session) -> pd.DataFrame:
    campaigns = db.query(Campaign).all()
    rows = []

    for campaign in campaigns:
        template = db.query(Template).get(campaign.template_id)
        segment = db.query(Segment).get(campaign.segment_id)
        targets = db.query(Target).filter(Target.segment_id == campaign.segment_id).all()

        for target in targets:
            delivered = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "delivered",
                )
                .scalar()
                or 0
            )
            opened = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "opened",
                )
                .scalar()
                or 0
            )
            clicked = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "clicked",
                )
                .scalar()
                or 0
            )
            reported = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "reported",
                )
                .scalar()
                or 0
            )

            rows.append(
                {
                    "source": "observed",
                    "campaign_id": campaign.id,
                    "campaign_status": campaign.status,
                    "campaign_channel": campaign.channel,
                    "campaign_launched_at": campaign.launched_at,
                    "template_id": template.id if template else None,
                    "template_name": template.name if template else None,
                    "template_subject": template.subject if template else None,
                    "template_description": template.description if template else None,
                    "signal_urgency": extract_signal(template.signals if template else None, "urgencia"),
                    "signal_authority": extract_signal(template.signals if template else None, "autoridad"),
                    "signal_reward": extract_signal(template.signals if template else None, "recompensa"),
                    "signal_personalization": extract_signal(template.signals if template else None, "personalizacion"),
                    "segment_id": segment.id if segment else None,
                    "age_bracket": segment.age_bracket if segment else None,
                    "gender": segment.gender if segment else None,
                    "education": segment.education if segment else None,
                    "target_id": target.id,
                    "target_recipient": target.recipient,
                    "target_uid": target.uid,
                    "delivered": delivered,
                    "opened": opened,
                    "clicked": clicked,
                    "reported": reported,
                    "opened_flag": 1 if opened > 0 else 0,
                    "clicked_flag": 1 if clicked > 0 else 0,
                    "reported_flag": 1 if reported > 0 else 0,
                }
            )

    return pd.DataFrame(rows)


def main():
    db = SessionLocal()
    try:
        dataset = build_dataset(db)

        csv_path = EXPORT_DIR / "analytic_dataset.csv"
        parquet_path = EXPORT_DIR / "analytic_dataset.parquet"

        dataset.to_csv(csv_path, index=False, encoding="utf-8")
        dataset.to_parquet(parquet_path, index=False)

        print(f"Dataset exportado a CSV: {csv_path.resolve()}")
        print(f"Dataset exportado a Parquet: {parquet_path.resolve()}")
        print(f"Filas exportadas: {len(dataset)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()