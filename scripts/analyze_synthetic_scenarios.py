from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from scripts.artifact_utils import (
    build_timestamp,
    build_artifact_name,
    latest_artifact,
)


EXPORT_DIR = Path("data/exports")


def rate(df: pd.DataFrame, column: str) -> float:

    if df.empty:
        return 0.0

    return (
        df[column].sum()
        / len(df)
        * 100
    )


def load_scenario(scenario: str) -> tuple[Path, pd.DataFrame]:

    path = latest_artifact(
        EXPORT_DIR,
        (
            "analytic_dataset_synthetic_"
            f"{scenario}-seed*_*.csv"
        ),
    )

    if path is None:
        raise FileNotFoundError(
            f"No se encontró dataset para: {scenario}"
        )

    return path, pd.read_csv(path)


def main():

    rows = []

    # ========================================================
    # CONTROL
    # ========================================================

    control_path, control = load_scenario(
        "control"
    )

    control_with = control[
        control["signal_personalization"] == 1
    ]

    control_without = control[
        control["signal_personalization"] == 0
    ]

    control_with_rate = rate(
        control_with,
        "opened_flag",
    )

    control_without_rate = rate(
        control_without,
        "opened_flag",
    )

    rows.append(
        {
            "scenario": "Control",
            "comparison": (
                "Apertura: personalización "
                "vs sin personalización"
            ),
            "group_a": "Con personalización",
            "group_a_rate_pct": round(
                control_with_rate,
                2,
            ),
            "group_b": "Sin personalización",
            "group_b_rate_pct": round(
                control_without_rate,
                2,
            ),
            "difference_pp": round(
                control_with_rate
                - control_without_rate,
                2,
            ),
            "expected_pattern": (
                "Sin diferencia deliberada"
            ),
        }
    )

    # ========================================================
    # PERSONALIZACIÓN
    # ========================================================

    personalization_path, personalization = (
        load_scenario("personalization")
    )

    personal_with = personalization[
        personalization[
            "signal_personalization"
        ] == 1
    ]

    personal_without = personalization[
        personalization[
            "signal_personalization"
        ] == 0
    ]

    personal_with_rate = rate(
        personal_with,
        "opened_flag",
    )

    personal_without_rate = rate(
        personal_without,
        "opened_flag",
    )

    rows.append(
        {
            "scenario": "Personalización",
            "comparison": (
                "Apertura: personalización "
                "vs sin personalización"
            ),
            "group_a": "Con personalización",
            "group_a_rate_pct": round(
                personal_with_rate,
                2,
            ),
            "group_b": "Sin personalización",
            "group_b_rate_pct": round(
                personal_without_rate,
                2,
            ),
            "difference_pp": round(
                personal_with_rate
                - personal_without_rate,
                2,
            ),
            "expected_pattern": (
                "Mayor apertura con personalización"
            ),
        }
    )

    # ========================================================
    # SEGMENTO
    # ========================================================

    segment_path, segment = load_scenario(
        "segment"
    )

    target_segment = segment[
        segment["experimental_target_segment"] == 1
    ]

    other_segments = segment[
        segment["experimental_target_segment"] == 0
    ]

    target_click_rate = rate(
        target_segment,
        "clicked_flag",
    )

    other_click_rate = rate(
        other_segments,
        "clicked_flag",
    )

    rows.append(
        {
            "scenario": "Segmento",
            "comparison": (
                "Clic: segmento experimental "
                "vs otros segmentos"
            ),
            "group_a": "Segmento experimental",
            "group_a_rate_pct": round(
                target_click_rate,
                2,
            ),
            "group_b": "Otros segmentos",
            "group_b_rate_pct": round(
                other_click_rate,
                2,
            ),
            "difference_pp": round(
                target_click_rate
                - other_click_rate,
                2,
            ),
            "expected_pattern": (
                "Mayor clic en segmento experimental"
            ),
        }
    )

    # ========================================================
    # INTERACCIÓN
    # ========================================================

    interaction_path, interaction = (
        load_scenario("interaction")
    )

    target_personalized = interaction[
        (
            interaction[
                "experimental_target_segment"
            ] == 1
        )
        &
        (
            interaction[
                "signal_personalization"
            ] == 1
        )
    ]

    target_not_personalized = interaction[
        (
            interaction[
                "experimental_target_segment"
            ] == 1
        )
        &
        (
            interaction[
                "signal_personalization"
            ] == 0
        )
    ]

    other_personalized = interaction[
        (
            interaction[
                "experimental_target_segment"
            ] == 0
        )
        &
        (
            interaction[
                "signal_personalization"
            ] == 1
        )
    ]

    other_not_personalized = interaction[
        (
            interaction[
                "experimental_target_segment"
            ] == 0
        )
        &
        (
            interaction[
                "signal_personalization"
            ] == 0
        )
    ]

    tp = rate(
        target_personalized,
        "opened_flag",
    )

    tn = rate(
        target_not_personalized,
        "opened_flag",
    )

    op = rate(
        other_personalized,
        "opened_flag",
    )

    on = rate(
        other_not_personalized,
        "opened_flag",
    )

    target_personalization_effect = tp - tn
    other_personalization_effect = op - on

    interaction_effect = (
        target_personalization_effect
        - other_personalization_effect
    )

    rows.append(
        {
            "scenario": "Interacción",
            "comparison": (
                "Efecto diferencial de "
                "personalización por segmento"
            ),
            "group_a": (
                "Efecto personalización "
                "en segmento experimental"
            ),
            "group_a_rate_pct": round(
                target_personalization_effect,
                2,
            ),
            "group_b": (
                "Efecto personalización "
                "en otros segmentos"
            ),
            "group_b_rate_pct": round(
                other_personalization_effect,
                2,
            ),
            "difference_pp": round(
                interaction_effect,
                2,
            ),
            "expected_pattern": (
                "Mayor efecto de personalización "
                "en segmento experimental"
            ),
        }
    )

    # ========================================================
    # EXPORTACIÓN
    # ========================================================

    summary = pd.DataFrame(rows)

    timestamp = build_timestamp()

    output_path = (
        EXPORT_DIR
        / build_artifact_name(
            artifact=(
                "synthetic_scenario_validation_summary"
            ),
            timestamp=timestamp,
            extension="csv",
        )
    )

    summary.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print()
    print("==========================================")
    print("VALIDACIÓN DE ESCENARIOS SINTÉTICOS")
    print("==========================================")
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("Archivos analizados:")
    print(f"Control: {control_path}")
    print(
        f"Personalización: "
        f"{personalization_path}"
    )
    print(f"Segmento: {segment_path}")
    print(f"Interacción: {interaction_path}")

    print()
    print(
        f"Resumen exportado en: "
        f"{output_path.resolve()}"
    )

    print("==========================================")
    print()


if __name__ == "__main__":
    main()