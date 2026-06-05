# scripts/compare_baseline_vs_xgboost.py
from __future__ import annotations

import json
import argparse
from pathlib import Path
import pandas as pd


MODEL_DIR = Path("data/models")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara métricas entre baseline logístico y XGBoost."
    )
    parser.add_argument(
        "--xgb-prefix",
        type=str,
        default="xgboost_combined",
        help="Prefijo de los artefactos de XGBoost.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    args = parse_args()

    baseline_metrics_path = MODEL_DIR / "baseline_logreg_metrics.json"
    xgb_metrics_path = MODEL_DIR / f"{args.xgb_prefix}_metrics.json"

    baseline = load_json(baseline_metrics_path)
    xgb = load_json(xgb_metrics_path)

    rows = [
        {
            "model": "baseline_logreg",
            "accuracy": baseline.get("accuracy"),
            "precision": baseline.get("precision"),
            "recall": baseline.get("recall"),
            "f1": baseline.get("f1"),
            "roc_auc": baseline.get("roc_auc"),
            "brier_score": baseline.get("brier_score"),
            "n_rows": baseline.get("n_rows"),
            "mode": baseline.get("mode"),
        },
        {
            "model": args.xgb_prefix,
            "accuracy": xgb.get("accuracy"),
            "precision": xgb.get("precision"),
            "recall": xgb.get("recall"),
            "f1": xgb.get("f1"),
            "roc_auc": xgb.get("roc_auc"),
            "brier_score": xgb.get("brier_score"),
            "n_rows": xgb.get("n_rows"),
            "mode": xgb.get("mode", "train_test_split"),
        },
    ]

    comparison_df = pd.DataFrame(rows)
    comparison_path = MODEL_DIR / "baseline_vs_xgboost_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False, encoding="utf-8")

    print(f"Comparación exportada en: {comparison_path.resolve()}")
    print(comparison_df)


if __name__ == "__main__":
    main()