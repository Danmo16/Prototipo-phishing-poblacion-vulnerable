# scripts/summarize_xgboost_results.py
from __future__ import annotations

import json
import argparse
from pathlib import Path
import pandas as pd


MODEL_DIR = Path("data/models")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un resumen académico del modelo XGBoost."
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="xgboost",
        help="Prefijo de los archivos exportados del modelo.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    metrics_path = MODEL_DIR / f"{args.prefix}_metrics.json"
    importance_path = MODEL_DIR / f"{args.prefix}_feature_importances.csv"
    output_path = MODEL_DIR / f"{args.prefix}_academic_summary.txt"

    if not metrics_path.exists() or not importance_path.exists():
        raise FileNotFoundError(
            f"Faltan artefactos del modelo con prefijo '{args.prefix}'. "
            f"Ejecuta primero: python -m scripts.train_xgboost_model --output-prefix {args.prefix}"
        )

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    importance_df = pd.read_csv(importance_path).head(10)

    lines = []
    lines.append("Resumen académico del modelo XGBoost")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Dataset utilizado: {metrics.get('dataset_path')}")
    lines.append(f"Dispositivo utilizado: {metrics.get('device')}")
    lines.append(f"Observaciones totales: {metrics.get('n_rows')}")
    lines.append(f"Observaciones de entrenamiento: {metrics.get('train_rows')}")
    lines.append(f"Observaciones de prueba: {metrics.get('test_rows')}")
    lines.append(f"Casos positivos totales: {metrics.get('positive_cases_total')}")
    lines.append(f"Accuracy: {metrics.get('accuracy')}")
    lines.append(f"Precision: {metrics.get('precision')}")
    lines.append(f"Recall: {metrics.get('recall')}")
    lines.append(f"F1-score: {metrics.get('f1')}")
    lines.append(f"ROC-AUC: {metrics.get('roc_auc')}")
    lines.append(f"Brier score: {metrics.get('brier_score')}")
    lines.append("")

    if "test_source_distribution" in metrics:
        lines.append("Distribución de fuentes en el conjunto de prueba:")
        for key, value in metrics["test_source_distribution"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.append("Variables con mayor importancia en XGBoost:")
    lines.append("")
    for _, row in importance_df.iterrows():
        lines.append(
            f"- {row['feature']}: importance={row['importance']:.6f}"
        )

    lines.append("")
    lines.append(
        "Interpretación sugerida: XGBoost permite estimar la probabilidad de clic "
        "a partir de variables demográficas y señales del mensaje. "
        "El Brier score complementa la evaluación al medir la calidad de calibración "
        "de las probabilidades predichas."
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen académico exportado en: {output_path.resolve()}")


if __name__ == "__main__":
    main()