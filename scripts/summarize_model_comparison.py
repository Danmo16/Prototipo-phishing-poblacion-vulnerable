# scripts/summarize_model_comparison.py
from __future__ import annotations

from pathlib import Path
import pandas as pd
import json


MODEL_DIR = Path("data/models")
OUTPUT_PATH = MODEL_DIR / "model_comparison_academic_summary.txt"


def main():
    metrics_path = MODEL_DIR / "model_comparison_metrics.csv"
    logreg_coef_path = MODEL_DIR / "logreg_coefficients.csv"
    tree_imp_path = MODEL_DIR / "decision_tree_importances.csv"
    summary_json_path = MODEL_DIR / "model_comparison_summary.json"

    if not metrics_path.exists():
        raise FileNotFoundError(
            "No existe model_comparison_metrics.csv. Ejecuta primero: python -m scripts.compare_models"
        )

    metrics_df = pd.read_csv(metrics_path)
    logreg_df = pd.read_csv(logreg_coef_path) if logreg_coef_path.exists() else pd.DataFrame()
    tree_df = pd.read_csv(tree_imp_path) if tree_imp_path.exists() else pd.DataFrame()

    summary_json = {}
    if summary_json_path.exists():
        with open(summary_json_path, "r", encoding="utf-8") as f:
            summary_json = json.load(f)

    lines = []
    lines.append("Comparación académica de modelos")
    lines.append("=" * 70)
    lines.append("")

    if summary_json:
        lines.append(f"Observaciones totales: {summary_json.get('n_rows_total')}")
        lines.append(f"Observaciones de entrenamiento: {summary_json.get('n_train')}")
        lines.append(f"Observaciones de prueba: {summary_json.get('n_test')}")
        lines.append(f"Casos positivos totales: {summary_json.get('positive_cases_total')}")
        lines.append("")

    lines.append("Métricas comparativas:")
    lines.append("")
    for _, row in metrics_df.iterrows():
        lines.append(
            f"- {row['model']}: accuracy={row['accuracy']}, "
            f"precision={row['precision']}, recall={row['recall']}, "
            f"f1={row['f1']}, roc_auc={row['roc_auc']}"
        )

    lines.append("")
    lines.append("Variables más influyentes - Regresión Logística:")
    lines.append("")
    if not logreg_df.empty:
        for _, row in logreg_df.head(10).iterrows():
            lines.append(
                f"- {row['feature']}: coef={row['coefficient']:.6f}, abs={row['abs_coefficient']:.6f}"
            )

    lines.append("")
    lines.append("Variables más influyentes - Árbol de Decisión:")
    lines.append("")
    if not tree_df.empty:
        for _, row in tree_df.head(10).iterrows():
            lines.append(
                f"- {row['feature']}: importance={row['importance']:.6f}"
            )

    lines.append("")
    lines.append(
        "Interpretación sugerida: la regresión logística ofrece mayor interpretabilidad "
        "a través de coeficientes, mientras que el árbol de decisión facilita una lectura "
        "más estructural de las variables importantes. La comparación entre ambos modelos "
        "permite sustentar la robustez del análisis de vulnerabilidad."
    )

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen comparativo exportado en: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()