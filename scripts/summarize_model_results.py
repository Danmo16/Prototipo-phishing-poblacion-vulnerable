# scripts/summarize_model_results.py
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


MODEL_DIR = Path("data/models")
OUTPUT_PATH = MODEL_DIR / "baseline_model_academic_summary.txt"


def main():
    metrics_path = MODEL_DIR / "baseline_logreg_metrics.json"
    coef_path = MODEL_DIR / "baseline_logreg_coefficients.csv"

    if not metrics_path.exists() or not coef_path.exists():
        raise FileNotFoundError(
            "Faltan artefactos del modelo. Ejecuta primero: python -m scripts.train_baseline_model"
        )

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    coef_df = pd.read_csv(coef_path).head(10)

    lines = []
    lines.append("Resumen académico del modelo baseline (Regresión Logística)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Modo de entrenamiento: {metrics.get('mode')}")
    lines.append(f"Número de observaciones: {metrics.get('n_rows')}")
    lines.append(f"Accuracy: {metrics.get('accuracy')}")
    lines.append(f"Precision: {metrics.get('precision')}")
    lines.append(f"Recall: {metrics.get('recall')}")
    lines.append(f"F1-score: {metrics.get('f1')}")
    lines.append(f"ROC-AUC: {metrics.get('roc_auc')}")
    lines.append("")
    lines.append("Variables con mayor peso absoluto en el modelo:")
    lines.append("")

    for _, row in coef_df.iterrows():
        lines.append(
            f"- {row['feature']}: coef={row['coefficient']:.6f} | abs={row['abs_coefficient']:.6f}"
        )

    lines.append("")
    lines.append(
        "Interpretación sugerida: los coeficientes positivos se asocian a una mayor "
        "probabilidad estimada de clic, mientras que los coeficientes negativos "
        "se asocian a una menor probabilidad, manteniendo constantes las demás variables."
    )

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Resumen académico exportado en: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()