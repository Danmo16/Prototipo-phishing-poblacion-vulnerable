# scripts/generate_synthetic_dataset.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import math
import random
import pandas as pd


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = EXPORT_DIR / "analytic_dataset_synthetic.csv"


random.seed(42)


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def sample_bernoulli(p: float) -> int:
    return 1 if random.random() < p else 0


def build_segments() -> list[dict]:
    segments = []
    segment_id = 1

    age_brackets = ["18-24", "25-34", "35-44", "45-54", "55+"]
    genders = ["F", "M"]
    educations = ["Secundaria", "Tecnica", "Universitaria", "Posgrado"]

    for age in age_brackets:
        for gender in genders:
            for education in educations:
                segments.append(
                    {
                        "segment_id": segment_id,
                        "age_bracket": age,
                        "gender": gender,
                        "education": education,
                    }
                )
                segment_id += 1

    return segments


def build_templates() -> list[dict]:
    return [
        {
            "template_id": 1,
            "template_name": "Urgencia",
            "template_subject": "Acción requerida",
            "template_description": "Plantilla con señal de urgencia",
            "signal_urgency": 1,
            "signal_authority": 0,
            "signal_reward": 0,
            "signal_personalization": 0,
        },
        {
            "template_id": 2,
            "template_name": "Autoridad",
            "template_subject": "Comunicado institucional",
            "template_description": "Plantilla con señal de autoridad",
            "signal_urgency": 0,
            "signal_authority": 1,
            "signal_reward": 0,
            "signal_personalization": 0,
        },
        {
            "template_id": 3,
            "template_name": "Recompensa",
            "template_subject": "Beneficio disponible",
            "template_description": "Plantilla con señal de recompensa",
            "signal_urgency": 0,
            "signal_authority": 0,
            "signal_reward": 1,
            "signal_personalization": 0,
        },
        {
            "template_id": 4,
            "template_name": "Personalización",
            "template_subject": "Actualización para usted",
            "template_description": "Plantilla con personalización",
            "signal_urgency": 0,
            "signal_authority": 0,
            "signal_reward": 0,
            "signal_personalization": 1,
        },
        {
            "template_id": 5,
            "template_name": "Urgencia + Autoridad",
            "template_subject": "Aviso urgente institucional",
            "template_description": "Plantilla combinada",
            "signal_urgency": 1,
            "signal_authority": 1,
            "signal_reward": 0,
            "signal_personalization": 0,
        },
        {
            "template_id": 6,
            "template_name": "Autoridad + Personalización",
            "template_subject": "Notificación importante para usted",
            "template_description": "Plantilla combinada",
            "signal_urgency": 0,
            "signal_authority": 1,
            "signal_reward": 0,
            "signal_personalization": 1,
        },
        {
            "template_id": 7,
            "template_name": "Recompensa + Personalización",
            "template_subject": "Beneficio exclusivo para usted",
            "template_description": "Plantilla combinada",
            "signal_urgency": 0,
            "signal_authority": 0,
            "signal_reward": 1,
            "signal_personalization": 1,
        },
        {
            "template_id": 8,
            "template_name": "Control neutro",
            "template_subject": "Información general",
            "template_description": "Plantilla sin señales fuertes",
            "signal_urgency": 0,
            "signal_authority": 0,
            "signal_reward": 0,
            "signal_personalization": 0,
        },
    ]


def age_effect(age_bracket: str) -> float:
    return {
        "18-24": 0.35,
        "25-34": 0.20,
        "35-44": 0.05,
        "45-54": -0.05,
        "55+": -0.10,
    }.get(age_bracket, 0.0)


def education_effect(education: str) -> float:
    return {
        "Secundaria": 0.30,
        "Tecnica": 0.15,
        "Universitaria": -0.05,
        "Posgrado": -0.15,
    }.get(education, 0.0)


def gender_effect(gender: str) -> float:
    return {
        "F": 0.02,
        "M": 0.00,
    }.get(gender, 0.0)


def open_probability(segment: dict, template: dict) -> float:
    score = -1.0
    score += age_effect(segment["age_bracket"])
    score += education_effect(segment["education"]) * 0.5
    score += gender_effect(segment["gender"])

    score += 0.20 * template["signal_personalization"]
    score += 0.12 * template["signal_authority"]
    score += 0.10 * template["signal_reward"]
    score += 0.08 * template["signal_urgency"]

    return min(max(sigmoid(score), 0.02), 0.95)


def click_probability(segment: dict, template: dict) -> float:
    score = -2.0
    score += age_effect(segment["age_bracket"]) * 0.9
    score += education_effect(segment["education"])
    score += gender_effect(segment["gender"])

    score += 0.30 * template["signal_urgency"]
    score += 0.28 * template["signal_authority"]
    score += 0.24 * template["signal_reward"]
    score += 0.18 * template["signal_personalization"]

    # interacción simple
    if template["signal_urgency"] == 1 and template["signal_authority"] == 1:
        score += 0.20

    return min(max(sigmoid(score), 0.01), 0.85)


def main():
    segments = build_segments()
    templates = build_templates()

    rows = []
    campaign_id = 1
    target_global_id = 1

    # parámetros ajustables
    campaigns_per_template = 10
    targets_per_segment_campaign = 30

    for template in templates:
        for _ in range(campaigns_per_template):
            # asignar segmento aleatorio a la campaña
            segment = random.choice(segments)

            for local_target_idx in range(targets_per_segment_campaign):
                recipient = f"synthetic_user_{target_global_id}@example.com"
                uid = f"synthetic-uid-{target_global_id}"

                p_open = open_probability(segment, template)
                p_click = click_probability(segment, template)

                delivered = 1
                opened_flag = sample_bernoulli(p_open)

                if opened_flag == 1:
                    clicked_flag = sample_bernoulli(p_click)
                else:
                    clicked_flag = 0

                rows.append(
                    {
                        "source": "synthetic",
                        "campaign_id": campaign_id,
                        "campaign_status": "launched",
                        "campaign_channel": "email",
                        "campaign_launched_at": None,
                        "template_id": template["template_id"],
                        "template_name": template["template_name"],
                        "template_subject": template["template_subject"],
                        "template_description": template["template_description"],
                        "signal_urgency": template["signal_urgency"],
                        "signal_authority": template["signal_authority"],
                        "signal_reward": template["signal_reward"],
                        "signal_personalization": template["signal_personalization"],
                        "segment_id": segment["segment_id"],
                        "age_bracket": segment["age_bracket"],
                        "gender": segment["gender"],
                        "education": segment["education"],
                        "target_id": target_global_id,
                        "target_recipient": recipient,
                        "target_uid": uid,
                        "delivered": delivered,
                        "opened": opened_flag,
                        "clicked": clicked_flag,
                        "opened_flag": opened_flag,
                        "clicked_flag": clicked_flag,
                    }
                )

                target_global_id += 1

            campaign_id += 1

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"Dataset sintético exportado en: {OUTPUT_PATH.resolve()}")
    print(f"Filas: {len(df)}")
    print("Distribución clicked_flag:")
    print(df["clicked_flag"].value_counts(dropna=False))
    print("Distribución opened_flag:")
    print(df["opened_flag"].value_counts(dropna=False))


if __name__ == "__main__":
    main()