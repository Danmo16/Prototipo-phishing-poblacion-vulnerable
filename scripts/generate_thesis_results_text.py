# scripts/generate_thesis_results_text.py
from __future__ import annotations

from pathlib import Path
import pandas as pd


EXPORT_DIR = Path("data/exports")
OUTPUT_PATH = EXPORT_DIR / "thesis_results_narrative.txt"


def main():
    general_path = EXPORT_DIR / "descriptive_general_table.csv"
    campaign_path = EXPORT_DIR / "descriptive_campaign_table.csv"
    segment_path = EXPORT_DIR / "descriptive_segment_table.csv"
    signal_path = EXPORT_DIR / "descriptive_signal_table.csv"

    if not all(p.exists() for p in [general_path, campaign_path, segment_path, signal_path]):
        raise FileNotFoundError(
            "Faltan archivos descriptivos. Ejecuta primero: python -m scripts.descriptive_analysis"
        )

    general_df = pd.read_csv(general_path)
    campaign_df = pd.read_csv(campaign_path)
    segment_df = pd.read_csv(segment_path)
    signal_df = pd.read_csv(signal_path)

    total_obs = int(general_df.loc[general_df["indicador"] == "Total de observaciones", "valor"].iloc[0])
    total_campaigns = int(general_df.loc[general_df["indicador"] == "Total de campañas", "valor"].iloc[0])
    total_targets = int(general_df.loc[general_df["indicador"] == "Total de targets", "valor"].iloc[0])
    delivered = int(general_df.loc[general_df["indicador"] == "Correos entregados", "valor"].iloc[0])
    opened = int(general_df.loc[general_df["indicador"] == "Aperturas registradas", "valor"].iloc[0])
    clicked = int(general_df.loc[general_df["indicador"] == "Clics registrados", "valor"].iloc[0])
    open_rate = float(general_df.loc[general_df["indicador"] == "Tasa de apertura (%)", "valor"].iloc[0])
    click_rate = float(general_df.loc[general_df["indicador"] == "Tasa de clic (%)", "valor"].iloc[0])

    best_campaign = campaign_df.sort_values("tasa_clic_pct", ascending=False).iloc[0] if not campaign_df.empty else None
    best_segment = segment_df.sort_values("tasa_clic_pct", ascending=False).iloc[0] if not segment_df.empty else None
    best_signal = signal_df.sort_values("tasa_clic_con_senal_pct", ascending=False).iloc[0] if not signal_df.empty else None

    lines = []
    lines.append("Redacción sugerida para el capítulo de resultados")
    lines.append("=" * 72)
    lines.append("")
    lines.append(
        f"Durante la ejecución del prototipo se consolidaron {total_obs} observaciones, "
        f"distribuidas en {total_campaigns} campañas y {total_targets} targets únicos. "
        f"En total se registraron {delivered} entregas, {opened} aperturas y {clicked} clics."
    )
    lines.append("")
    lines.append(
        f"La tasa global de apertura alcanzó {open_rate}% y la tasa global de clic fue de {click_rate}%, "
        f"lo cual permite evidenciar que el prototipo ya cuenta con capacidad para capturar y estructurar "
        f"las interacciones de los usuarios frente a campañas simuladas."
    )
    lines.append("")

    if best_campaign is not None:
        lines.append(
            f"Al analizar el comportamiento por campaña, se identificó que la campaña "
            f"{int(best_campaign['campaign_id'])} presentó la mayor tasa de clic "
            f"({best_campaign['tasa_clic_pct']}%), lo que la ubica como la campaña de mayor "
            f"respuesta entre las observadas en este corte."
        )
        lines.append("")

    if best_segment is not None:
        lines.append(
            f"Desde el enfoque demográfico, el segmento {int(best_segment['segment_id'])} "
            f"(edad: {best_segment['age_bracket']}, género: {best_segment['gender']}, "
            f"educación: {best_segment['education']}) mostró la mayor tasa de clic "
            f"({best_segment['tasa_clic_pct']}%), sugiriendo una mayor susceptibilidad relativa "
            f"dentro de los segmentos evaluados."
        )
        lines.append("")

    if best_signal is not None:
        lines.append(
            f"En relación con las señales de las plantillas, la señal {best_signal['senal']} "
            f"mostró la mayor tasa de clic cuando estuvo presente "
            f"({best_signal['tasa_clic_con_senal_pct']}%), lo que sugiere que este disparador "
            f"podría tener una mayor capacidad de influencia sobre el comportamiento del usuario."
        )
        lines.append("")

    lines.append(
        "Aunque estos resultados corresponden a una fase preliminar del prototipo, constituyen "
        "una base relevante para la identificación de patrones iniciales de vulnerabilidad y para "
        "el ajuste del diseño experimental antes de realizar pruebas en escenarios más amplios."
    )

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Texto de resultados exportado en: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()