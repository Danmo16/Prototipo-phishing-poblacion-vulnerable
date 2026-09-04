from __future__ import annotations

import sys
import argparse
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from scripts.artifact_utils import (
    build_timestamp,
    build_artifact_name,
)


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Segmentos experimentales
# ============================================================

def build_experimental_segments() -> list[dict]:
    """
    Se utilizan cinco segmentos controlados para garantizar
    una distribución balanceada dentro de cada escenario.
    """

    return [
        {
            "segment_id": 1,
            "age_bracket": "18-24",
            "gender": "F",
            "education": "Secundaria",
        },
        {
            "segment_id": 2,
            "age_bracket": "25-34",
            "gender": "M",
            "education": "Tecnica",
        },
        {
            "segment_id": 3,
            "age_bracket": "35-44",
            "gender": "F",
            "education": "Universitaria",
        },
        {
            "segment_id": 4,
            "age_bracket": "45-54",
            "gender": "M",
            "education": "Posgrado",
        },
        {
            "segment_id": 5,
            "age_bracket": "55+",
            "gender": "F",
            "education": "Universitaria",
        },
    ]


# ============================================================
# Plantillas experimentales
# ============================================================

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


# ============================================================
# Utilidades
# ============================================================

def sample_bernoulli(probability: float) -> int:
    return 1 if random.random() < probability else 0


# ============================================================
# Probabilidades experimentales
# ============================================================

def get_probabilities(
    scenario: str,
    segment: dict,
    template: dict,
) -> tuple[float, float]:

    """
    Retorna:

    p_open:
        Probabilidad de apertura.

    p_click_given_open:
        Probabilidad de clic condicionada a que
        el mensaje haya sido abierto.

    IMPORTANTE:
    Estas probabilidades son parámetros artificiales
    utilizados únicamente para comprobar si la capa
    analítica recupera patrones conocidos.
    """

    # --------------------------------------------------------
    # Escenario 1: CONTROL
    # --------------------------------------------------------
    # Ninguna señal ni segmento debe tener un efecto
    # deliberadamente introducido.
    if scenario == "control":
        p_open = 0.32
        p_click_given_open = 0.18

        return p_open, p_click_given_open

    # --------------------------------------------------------
    # Escenario 2: PERSONALIZACIÓN
    # --------------------------------------------------------
    # Se introduce deliberadamente una mayor probabilidad
    # de apertura cuando la plantilla está personalizada.
    if scenario == "personalization":

        if template["signal_personalization"] == 1:
            p_open = 0.48
        else:
            p_open = 0.26

        p_click_given_open = 0.18

        return p_open, p_click_given_open

    # --------------------------------------------------------
    # Escenario 3: DIFERENCIA ENTRE SEGMENTOS
    # --------------------------------------------------------
    # El segmento 1 se utiliza exclusivamente como grupo
    # experimental. No representa una población realmente
    # vulnerable.
    if scenario == "segment":

        p_open = 0.32

        if segment["segment_id"] == 1:
            p_click_given_open = 0.35
        else:
            p_click_given_open = 0.12

        return p_open, p_click_given_open

    # --------------------------------------------------------
    # Escenario 4: INTERACCIÓN
    # --------------------------------------------------------
    # Se introduce un efecto distinto de personalización
    # dependiendo de si el registro pertenece o no al
    # segmento experimental.
    if scenario == "interaction":

        is_target_segment = segment["segment_id"] == 1
        is_personalized = (
            template["signal_personalization"] == 1
        )

        if is_target_segment and is_personalized:
            p_open = 0.60

        elif is_personalized:
            p_open = 0.40

        elif is_target_segment:
            p_open = 0.30

        else:
            p_open = 0.25

        p_click_given_open = 0.18

        return p_open, p_click_given_open

    raise ValueError(
        f"Escenario no reconocido: {scenario}"
    )


# ============================================================
# Argumentos
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Generación de escenarios sintéticos controlados "
            "para validación analítica del prototipo."
        )
    )

    parser.add_argument(
        "--scenario",
        required=True,
        choices=[
            "control",
            "personalization",
            "segment",
            "interaction",
        ],
        help="Escenario experimental que será generado.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla de generación aleatoria.",
    )

    parser.add_argument(
        "--targets-per-cell",
        type=int,
        default=15,
        help=(
            "Número de targets por combinación "
            "segmento-plantilla."
        ),
    )

    return parser.parse_args()


# ============================================================
# Generación del escenario
# ============================================================

def main():

    args = parse_args()

    random.seed(args.seed)

    segments = build_experimental_segments()
    templates = build_templates()

    rows = []

    campaign_id = 1
    target_global_id = 1

    for template in templates:

        for segment in segments:

            # Cada combinación template-segmento se considera
            # una campaña sintética independiente.
            for _ in range(args.targets_per_cell):

                recipient = (
                    f"synthetic_{args.scenario}_"
                    f"user_{target_global_id}@example.com"
                )

                uid = (
                    f"synthetic-{args.scenario}-"
                    f"uid-{target_global_id}"
                )

                p_open, p_click_given_open = get_probabilities(
                    args.scenario,
                    segment,
                    template,
                )

                delivered = 1

                opened_flag = sample_bernoulli(
                    p_open
                )

                if opened_flag == 1:
                    clicked_flag = sample_bernoulli(
                        p_click_given_open
                    )
                else:
                    clicked_flag = 0

                reported_flag = 0

                rows.append(
                    {
                        "source": "synthetic_scenario",
                        "scenario": args.scenario,
                        "scenario_seed": args.seed,

                        "campaign_id": campaign_id,
                        "campaign_status": "launched",
                        "campaign_channel": "email",
                        "campaign_launched_at": None,

                        "template_id": template["template_id"],
                        "template_name": template["template_name"],
                        "template_subject": template["template_subject"],
                        "template_description": template[
                            "template_description"
                        ],

                        "signal_urgency": template[
                            "signal_urgency"
                        ],
                        "signal_authority": template[
                            "signal_authority"
                        ],
                        "signal_reward": template[
                            "signal_reward"
                        ],
                        "signal_personalization": template[
                            "signal_personalization"
                        ],

                        "segment_id": segment["segment_id"],
                        "age_bracket": segment["age_bracket"],
                        "gender": segment["gender"],
                        "education": segment["education"],

                        "experimental_target_segment": (
                            1
                            if segment["segment_id"] == 1
                            else 0
                        ),

                        "target_id": target_global_id,
                        "target_recipient": recipient,
                        "target_uid": uid,

                        "delivered": delivered,

                        "opened": opened_flag,
                        "clicked": clicked_flag,
                        "reported": reported_flag,

                        "opened_flag": opened_flag,
                        "clicked_flag": clicked_flag,
                        "reported_flag": reported_flag,

                        "expected_open_probability": p_open,

                        (
                            "expected_click_given_open_probability"
                        ): p_click_given_open,
                    }
                )

                target_global_id += 1

            campaign_id += 1

    df = pd.DataFrame(rows)

    timestamp = build_timestamp()

    output_path = (
        EXPORT_DIR
        / build_artifact_name(
            artifact="analytic_dataset_synthetic",
            context=(
                f"{args.scenario}-seed{args.seed}"
            ),
            timestamp=timestamp,
            extension="csv",
        )
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print()
    print("==========================================")
    print("ESCENARIO SINTÉTICO GENERADO")
    print("==========================================")
    print(f"Escenario: {args.scenario}")
    print(f"Semilla: {args.seed}")
    print(
        f"Targets por combinación: "
        f"{args.targets_per_cell}"
    )
    print(f"Filas generadas: {len(df)}")
    print(f"Campañas sintéticas: {df['campaign_id'].nunique()}")
    print(f"Segmentos: {df['segment_id'].nunique()}")
    print(f"Plantillas: {df['template_id'].nunique()}")

    print(
        f"Tasa apertura: "
        f"{df['opened_flag'].mean() * 100:.2f}%"
    )

    print(
        f"Tasa clic: "
        f"{df['clicked_flag'].mean() * 100:.2f}%"
    )

    print(f"Archivo: {output_path.resolve()}")
    print("==========================================")
    print()


if __name__ == "__main__":
    main()