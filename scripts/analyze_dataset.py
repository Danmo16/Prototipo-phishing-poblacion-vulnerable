# scripts/analyze_dataset.py
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


def build_global_summary(df: pd.DataFrame) -> pd.DataFrame:
    delivered = int(df["delivered"].sum())
    opened = int(df["opened_flag"].sum())
    clicked = int(df["clicked_flag"].sum())

    rows = [
        {"indicator": "total_rows", "value": len(df)},
        {"indicator": "total_campaigns", "value": df["campaign_id"].nunique()},
        {"indicator": "total_targets", "value": df["target_id"].nunique()},
        {"indicator": "total_segments", "value": df["segment_id"].nunique()},
        {"indicator": "total_templates", "value": df["template_id"].nunique()},
        {"indicator": "total_delivered", "value": delivered},
        {"indicator": "total_opened", "value": opened},
        {"indicator": "total_clicked", "value": clicked},
        {"indicator": "open_rate_pct", "value": safe_rate(opened, delivered)},
        {"indicator": "click_rate_pct", "value": safe_rate(clicked, delivered)},
    ]
    return pd.DataFrame(rows)


def build_campaign_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            ["campaign_id", "campaign_status", "campaign_channel", "segment_id", "template_id"],
            dropna=False
        )
        .agg(
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["click_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    return grouped.sort_values("campaign_id")


def build_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            ["segment_id", "age_bracket", "gender", "education"],
            dropna=False
        )
        .agg(
            targets=("target_id", "nunique"),
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["click_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    return grouped.sort_values("segment_id")


def build_signal_summary(df: pd.DataFrame) -> pd.DataFrame:
    signal_columns = [
        "signal_urgency",
        "signal_authority",
        "signal_reward",
        "signal_personalization",
    ]

    rows = []
    for signal in signal_columns:
        with_signal = df[df[signal] == 1]
        without_signal = df[df[signal] == 0]

        rows.append(
            {
                "signal": signal,
                "rows_with_signal": len(with_signal),
                "delivered_with_signal": int(with_signal["delivered"].sum()),
                "opened_with_signal": int(with_signal["opened_flag"].sum()),
                "clicked_with_signal": int(with_signal["clicked_flag"].sum()),
                "open_rate_with_signal_pct": safe_rate(
                    with_signal["opened_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "click_rate_with_signal_pct": safe_rate(
                    with_signal["clicked_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "rows_without_signal": len(without_signal),
                "delivered_without_signal": int(without_signal["delivered"].sum()),
                "opened_without_signal": int(without_signal["opened_flag"].sum()),
                "clicked_without_signal": int(without_signal["clicked_flag"].sum()),
                "open_rate_without_signal_pct": safe_rate(
                    without_signal["opened_flag"].sum(),
                    without_signal["delivered"].sum(),
                ),
                "click_rate_without_signal_pct": safe_rate(
                    without_signal["clicked_flag"].sum(),
                    without_signal["delivered"].sum(),
                ),
            }
        )

    return pd.DataFrame(rows)


def build_template_summary(df: pd.DataFrame) -> pd.DataFrame:
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
            dropna=False
        )
        .agg(
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["click_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    return grouped.sort_values("template_id")


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DATASET_PATH}. Ejecuta primero: python -m scripts.export_dataset"
        )

    df = pd.read_csv(DATASET_PATH)

    global_summary = build_global_summary(df)
    campaign_summary = build_campaign_summary(df)
    segment_summary = build_segment_summary(df)
    signal_summary = build_signal_summary(df)
    template_summary = build_template_summary(df)

    global_summary.to_csv(EXPORT_DIR / "analysis_global_summary.csv", index=False, encoding="utf-8")
    campaign_summary.to_csv(EXPORT_DIR / "analysis_campaign_summary.csv", index=False, encoding="utf-8")
    segment_summary.to_csv(EXPORT_DIR / "analysis_segment_summary.csv", index=False, encoding="utf-8")
    signal_summary.to_csv(EXPORT_DIR / "analysis_signal_summary.csv", index=False, encoding="utf-8")
    template_summary.to_csv(EXPORT_DIR / "analysis_template_summary.csv", index=False, encoding="utf-8")

    print("Análisis exportado correctamente en data/exports/")
    print(f"- {EXPORT_DIR / 'analysis_global_summary.csv'}")
    print(f"- {EXPORT_DIR / 'analysis_campaign_summary.csv'}")
    print(f"- {EXPORT_DIR / 'analysis_segment_summary.csv'}")
    print(f"- {EXPORT_DIR / 'analysis_signal_summary.csv'}")
    print(f"- {EXPORT_DIR / 'analysis_template_summary.csv'}")


if __name__ == "__main__":
    main()