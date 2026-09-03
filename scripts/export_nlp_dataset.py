# scripts/export_nlp_dataset.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import re
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.db.session import SessionLocal
from core.domain.models import Campaign, Event, Segment, Target, Template

from scripts.artifact_utils import (
    build_timestamp,
    build_artifact_name,
)


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_dataset(db: Session) -> pd.DataFrame:
    campaigns = db.query(Campaign).all()
    rows = []

    for campaign in campaigns:
        template = db.query(Template).get(campaign.template_id)
        segment = db.query(Segment).get(campaign.segment_id)
        targets = db.query(Target).filter(Target.segment_id == campaign.segment_id).all()

        for target in targets:
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

            subject = template.subject if template else ""
            description = template.description if template else ""
            html_body = template.html_body if template else ""
            html_text = html_to_text(html_body)

            text_input = " [SEP] ".join(
                [
                    str(subject or ""),
                    str(description or ""),
                    str(html_text or ""),
                ]
            ).strip()

            rows.append(
                {
                    "campaign_id": campaign.id,
                    "segment_id": segment.id if segment else None,
                    "target_id": target.id,
                    "template_id": template.id if template else None,
                    "template_subject": subject,
                    "template_description": description,
                    "template_html_text": html_text,
                    "text_input": text_input,
                    "clicked_flag": 1 if clicked > 0 else 0,
                }
            )

    return pd.DataFrame(rows)


def main():
    db = SessionLocal()
    try:
        df = build_dataset(db)

        timestamp = build_timestamp()

        csv_path = EXPORT_DIR / build_artifact_name(
            artifact="nlp_dataset",
            timestamp=timestamp,
            extension="csv",
        )
        parquet_path = EXPORT_DIR / build_artifact_name(
            artifact="nlp_dataset",
            timestamp=timestamp,
            extension="parquet",
        )

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_parquet(parquet_path, index=False)

        print(f"NLP dataset exportado a CSV: {csv_path.resolve()}")
        print(f"NLP dataset exportado a Parquet: {parquet_path.resolve()}")
        print(f"Filas exportadas: {len(df)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()