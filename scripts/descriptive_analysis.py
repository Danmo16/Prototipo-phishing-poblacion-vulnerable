# scripts/descriptive_analysis.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PATH = EXPORT_DIR / "analytic_dataset.csv"


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def build_general_table(df: pd.DataFrame) -> pd.DataFrame:
    delivered = int(df["delivered"].sum())
    opened = int(df["opened_flag"].sum())
    clicked = int(df["clicked_flag"].sum())
    reported = int(df["reported_flag"].sum()) if "reported_flag" in df.columns else 0

    rows = [
        {"indicador": "Total de observaciones", "valor": len(df)},
        {"indicador": "Total de campañas", "valor": df["campaign_id"].nunique()},
        {"indicador": "Total de targets", "valor": df["target_id"].nunique()},
        {"indicador": "Total de segmentos", "valor": df["segment_id"].nunique()},
        {"indicador": "Total de plantillas", "valor": df["template_id"].nunique()},
        {"indicador": "Correos entregados", "valor": delivered},
        {"indicador": "Aperturas registradas", "valor": opened},
        {"indicador": "Clics registrados", "valor": clicked},
        {"indicador": "Reportes registrados", "valor": reported},
        {"indicador": "Tasa de apertura (%)", "valor": safe_rate(opened, delivered)},
        {"indicador": "Tasa de clic (%)", "valor": safe_rate(clicked, delivered)},
        {"indicador": "Tasa de reporte (%)", "valor": safe_rate(reported, delivered)},
    ]
    return pd.DataFrame(rows)


def build_campaign_table(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            ["campaign_id", "campaign_status", "campaign_channel", "segment_id", "template_id"],
            dropna=False,
        )
        .agg(
            observaciones=("target_id", "count"),
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
            reported=("reported_flag", "sum"),
        )
        .reset_index()
    )

    grouped["tasa_apertura_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["tasa_clic_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    grouped["tasa_reporte_pct"] = grouped.apply(
        lambda r: safe_rate(r["reported"], r["delivered"]), axis=1
    )
    return grouped.sort_values("campaign_id")


def build_segment_table(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            ["segment_id", "age_bracket", "gender", "education"],
            dropna=False,
        )
        .agg(
            targets=("target_id", "nunique"),
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
            reported=("reported_flag", "sum"),
        )
        .reset_index()
    )

    grouped["tasa_apertura_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["tasa_clic_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    grouped["tasa_reporte_pct"] = grouped.apply(
        lambda r: safe_rate(r["reported"], r["delivered"]), axis=1
    )
    return grouped.sort_values("segment_id")


def build_template_table(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            [
                "template_id",
                "template_name",
                "template_subject",
                "template_description",
                "signal_urgency",
                "signal_authority",
                "signal_reward",
                "signal_personalization",
            ],
            dropna=False,
        )
        .agg(
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
            reported=("reported_flag", "sum"),
        )
        .reset_index()
    )

    grouped["tasa_apertura_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["tasa_clic_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    grouped["tasa_reporte_pct"] = grouped.apply(
        lambda r: safe_rate(r["reported"], r["delivered"]), axis=1
    )
    return grouped.sort_values("template_id")


def build_signal_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    signal_map = {
        "signal_urgency": "Urgencia",
        "signal_authority": "Autoridad",
        "signal_reward": "Recompensa",
        "signal_personalization": "Personalización",
    }

    for col, label in signal_map.items():
        with_signal = df[df[col] == 1]
        without_signal = df[df[col] == 0]

        rows.append(
            {
                "senal": label,
                "observaciones_con_senal": len(with_signal),
                "delivered_con_senal": int(with_signal["delivered"].sum()),
                "opened_con_senal": int(with_signal["opened_flag"].sum()),
                "clicked_con_senal": int(with_signal["clicked_flag"].sum()),
                "reported_con_senal": int(with_signal["reported_flag"].sum()),
                "tasa_apertura_con_senal_pct": safe_rate(
                    with_signal["opened_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "tasa_clic_con_senal_pct": safe_rate(
                    with_signal["clicked_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "tasa_reporte_con_senal_pct": safe_rate(
                    with_signal["reported_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "observaciones_sin_senal": len(without_signal),
                "delivered_sin_senal": int(without_signal["delivered"].sum()),
                "opened_sin_senal": int(without_signal["opened_flag"].sum()),
                "clicked_sin_senal": int(without_signal["clicked_flag"].sum()),
                "reported_sin_senal": int(without_signal["reported_flag"].sum()),
                "tasa_apertura_sin_senal_pct": safe_rate(
                    without_signal["opened_flag"].sum(),
                    without_signal["delivered"].sum(),
                ),
                "tasa_clic_sin_senal_pct": safe_rate(
                    without_signal["clicked_flag"].sum(),
                    without_signal["delivered"].sum(),
                ),
                "tasa_reporte_sin_senal_pct": safe_rate(
                    without_signal["reported_flag"].sum(),
                    without_signal["delivered"].sum(),
                ),
            }
        )

    return pd.DataFrame(rows)


def build_conclusions_text(
    general_df: pd.DataFrame,
    campaign_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    signal_df: pd.DataFrame,
) -> str:
    lines: list[str] = []

    lines.append("Análisis estadístico descriptivo formal")
    lines.append("=" * 72)
    lines.append("")

    total_obs = int(general_df.loc[general_df["indicador"] == "Total de observaciones", "valor"].iloc[0])
    total_campaigns = int(general_df.loc[general_df["indicador"] == "Total de campañas", "valor"].iloc[0])
    total_targets = int(general_df.loc[general_df["indicador"] == "Total de targets", "valor"].iloc[0])
    open_rate = float(general_df.loc[general_df["indicador"] == "Tasa de apertura (%)", "valor"].iloc[0])
    click_rate = float(general_df.loc[general_df["indicador"] == "Tasa de clic (%)", "valor"].iloc[0])
    report_rate = float(general_df.loc[general_df["indicador"] == "Tasa de reporte (%)", "valor"].iloc[0])

    lines.append(
        f"En el corte analizado se registraron {total_obs} observaciones, "
        f"correspondientes a {total_campaigns} campañas y {total_targets} targets únicos. "
        f"La tasa global de apertura fue de {open_rate}%, la tasa global de clic fue de {click_rate}% "
        f"y la tasa global de reporte fue de {report_rate}%."
    )
    lines.append("")

    if not campaign_df.empty:
        best_campaign = campaign_df.sort_values("tasa_clic_pct", ascending=False).iloc[0]
        lines.append(
            f"La campaña con mayor tasa de clic fue la campaña {int(best_campaign['campaign_id'])}, "
            f"con una tasa de clic de {best_campaign['tasa_clic_pct']}% y una tasa de reporte de "
            f"{best_campaign['tasa_reporte_pct']}%."
        )
        lines.append("")

    if not segment_df.empty:
        best_segment = segment_df.sort_values("tasa_clic_pct", ascending=False).iloc[0]
        lines.append(
            f"Desde la perspectiva demográfica, el segmento con mayor tasa de clic fue el segmento "
            f"{int(best_segment['segment_id'])} "
            f"(edad: {best_segment['age_bracket']}, género: {best_segment['gender']}, "
            f"educación: {best_segment['education']}), con una tasa de clic de "
            f"{best_segment['tasa_clic_pct']}%."
        )
        lines.append("")

    if not signal_df.empty:
        best_signal = signal_df.sort_values("tasa_clic_con_senal_pct", ascending=False).iloc[0]
        lines.append(
            f"En cuanto a las señales del mensaje, la señal con mayor tasa de clic cuando estuvo activa fue "
            f"{best_signal['senal']}, alcanzando una tasa de clic de "
            f"{best_signal['tasa_clic_con_senal_pct']}%."
        )
        lines.append("")

    lines.append(
        "Estos resultados deben interpretarse como evidencia descriptiva preliminar. "
        "A medida que se incorporen nuevas observaciones y campañas, será posible fortalecer la "
        "estabilidad de las tasas y realizar análisis comparativos más robustos."
    )

    return "\n".join(lines)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DATASET_PATH}. Ejecuta primero: python -m scripts.export_dataset"
        )

    df = pd.read_csv(DATASET_PATH)

    general_df = build_general_table(df)
    campaign_df = build_campaign_table(df)
    segment_df = build_segment_table(df)
    template_df = build_template_table(df)
    signal_df = build_signal_table(df)

    conclusions_text = build_conclusions_text(
        general_df=general_df,
        campaign_df=campaign_df,
        segment_df=segment_df,
        signal_df=signal_df,
    )

    general_df.to_csv(EXPORT_DIR / "descriptive_general_table.csv", index=False, encoding="utf-8")
    campaign_df.to_csv(EXPORT_DIR / "descriptive_campaign_table.csv", index=False, encoding="utf-8")
    segment_df.to_csv(EXPORT_DIR / "descriptive_segment_table.csv", index=False, encoding="utf-8")
    template_df.to_csv(EXPORT_DIR / "descriptive_template_table.csv", index=False, encoding="utf-8")
    signal_df.to_csv(EXPORT_DIR / "descriptive_signal_table.csv", index=False, encoding="utf-8")
    (EXPORT_DIR / "descriptive_conclusions.txt").write_text(conclusions_text, encoding="utf-8")

    print("Análisis descriptivo exportado correctamente en data/exports/")
    print(f"- {EXPORT_DIR / 'descriptive_general_table.csv'}")
    print(f"- {EXPORT_DIR / 'descriptive_campaign_table.csv'}")
    print(f"- {EXPORT_DIR / 'descriptive_segment_table.csv'}")
    print(f"- {EXPORT_DIR / 'descriptive_template_table.csv'}")
    print(f"- {EXPORT_DIR / 'descriptive_signal_table.csv'}")
    print(f"- {EXPORT_DIR / 'descriptive_conclusions.txt'}")


if __name__ == "__main__":
    main()