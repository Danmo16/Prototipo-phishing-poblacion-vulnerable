# scripts/generate_sampling_plan.py
from __future__ import annotations

import sys
import argparse
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy.orm import Session

from core.db.session import SessionLocal
from core.domain.models import Segment, Template, Target


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un plan de muestreo y aleatorización balanceado."
    )
    parser.add_argument(
        "--campaigns-per-template",
        type=int,
        default=2,
        help="Número de campañas objetivo por template.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla de aleatorización.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(EXPORT_DIR / "sampling_plan.csv"),
        help="Ruta del CSV de salida.",
    )
    return parser.parse_args()


def get_target_count_by_segment(db: Session) -> dict[int, int]:
    rows = db.query(Target.segment_id).all()
    counts: dict[int, int] = {}
    for (segment_id,) in rows:
        counts[segment_id] = counts.get(segment_id, 0) + 1
    return counts


def main():
    args = parse_args()
    random.seed(args.seed)

    db: Session = SessionLocal()
    try:
        segments = db.query(Segment).order_by(Segment.id.asc()).all()
        templates = db.query(Template).filter(Template.channel == "email").order_by(Template.id.asc()).all()
        target_counts = get_target_count_by_segment(db)

        if not segments:
            raise ValueError("No hay segmentos en la base de datos.")
        if not templates:
            raise ValueError("No hay templates de email en la base de datos.")

        eligible_segments = [s for s in segments if target_counts.get(s.id, 0) > 0]
        if not eligible_segments:
            raise ValueError("No hay segmentos con targets asociados.")

        segment_pool = eligible_segments.copy()
        random.shuffle(segment_pool)

        plan_rows = []
        assignment_id = 1

        for template in templates:
            for repetition in range(1, args.campaigns_per_template + 1):
                if not segment_pool:
                    segment_pool = eligible_segments.copy()
                    random.shuffle(segment_pool)

                segment = segment_pool.pop()

                plan_rows.append(
                    {
                        "assignment_id": assignment_id,
                        "template_id": template.id,
                        "template_name": template.name,
                        "template_subject": template.subject,
                        "signal_urgency": 1 if (template.signals or {}).get("urgencia", 0) in [1, True, "1", "true", "True"] else 0,
                        "signal_authority": 1 if (template.signals or {}).get("autoridad", 0) in [1, True, "1", "true", "True"] else 0,
                        "signal_reward": 1 if (template.signals or {}).get("recompensa", 0) in [1, True, "1", "true", "True"] else 0,
                        "signal_personalization": 1 if (template.signals or {}).get("personalizacion", 0) in [1, True, "1", "true", "True"] else 0,
                        "segment_id": segment.id,
                        "age_bracket": segment.age_bracket,
                        "gender": segment.gender,
                        "education": segment.education,
                        "segment_target_count": target_counts.get(segment.id, 0),
                        "campaign_channel": "email",
                        "repetition": repetition,
                        "random_seed": args.seed,
                        "status": "planned",
                    }
                )
                assignment_id += 1

        plan_df = pd.DataFrame(plan_rows)

        # Barajar el orden final del plan manteniendo reproducibilidad
        plan_df = plan_df.sample(frac=1, random_state=args.seed).reset_index(drop=True)
        plan_df["execution_order"] = range(1, len(plan_df) + 1)

        output_path = Path(args.output)
        plan_df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"Plan de muestreo exportado en: {output_path.resolve()}")
        print(f"Filas del plan: {len(plan_df)}")
        print(plan_df.head(10))

    finally:
        db.close()


if __name__ == "__main__":
    main()