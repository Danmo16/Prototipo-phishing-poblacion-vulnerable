# scripts/materialize_sampling_plan.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy.orm import Session

from core.db.session import SessionLocal
from core.domain.models import Campaign, Segment, Template


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PLAN_PATH = EXPORT_DIR / "sampling_plan.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materializa campañas en BD a partir de un plan de muestreo."
    )
    parser.add_argument(
        "--plan",
        type=str,
        default=str(DEFAULT_PLAN_PATH),
        help="Ruta del CSV con el plan de muestreo.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Número máximo de campañas a crear.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise FileNotFoundError(
            f"No existe {plan_path}. Ejecuta primero: python -m scripts.generate_sampling_plan"
        )

    plan_df = pd.read_csv(plan_path)
    if args.limit is not None:
        plan_df = plan_df.head(args.limit)

    db: Session = SessionLocal()
    created_rows = []

    try:
        for _, row in plan_df.iterrows():
            template = db.query(Template).get(int(row["template_id"]))
            if not template:
                print(f"Template no encontrado: {row['template_id']}. Se omite.")
                continue

            segment = db.query(Segment).get(int(row["segment_id"]))
            if not segment:
                print(f"Segment no encontrado: {row['segment_id']}. Se omite.")
                continue

            campaign = Campaign(
                channel=row["campaign_channel"],
                template_id=int(row["template_id"]),
                segment_id=int(row["segment_id"]),
                status="draft",
            )
            db.add(campaign)
            db.flush()

            created_rows.append(
                {
                    "assignment_id": int(row["assignment_id"]),
                    "campaign_id": campaign.id,
                    "template_id": int(row["template_id"]),
                    "segment_id": int(row["segment_id"]),
                    "execution_order": int(row["execution_order"]),
                    "status": "created",
                }
            )

        db.commit()

        created_df = pd.DataFrame(created_rows)
        output_path = EXPORT_DIR / "materialized_campaigns.csv"
        created_df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"Campañas materializadas correctamente.")
        print(f"Archivo exportado: {output_path.resolve()}")
        print(f"Total campañas creadas: {len(created_df)}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()