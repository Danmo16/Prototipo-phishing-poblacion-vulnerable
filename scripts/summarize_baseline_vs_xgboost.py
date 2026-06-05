# scripts/summarize_baseline_vs_xgboost.py
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


MODEL_DIR = Path("data/models")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera resumen académico comparativo entre baseline y XGBoost."
    )
    parser.add_argument(
        "--xgb-prefix",
        type=str,
        default="xgboost_combined",
        help="Prefijo de XGBoost usado en la comparación.",
    )
    return parser.parse_args()


def best_model_text(metric_name: str, baseline_value, xgb_value, higher_is_better: bool = True) -> str:
    if baseline_value is None or xgb_value is None:
        return f"No fue posible comparar {metric_name} por ausencia de datos completos."

    if higher_is_better:
        if xgb_value > baseline_value:
            return f"XGBoost superó al baseline en {metric_name}."
        elif xgb_value < baseline_value:
            return f"La regresión logística baseline superó a XGBoost en {metric_name}."
        return f"Ambos modelos presentaron el mismo valor en {metric_name}."
    else:
        if xgb_value < baseline_value:
            return f"XGBoost presentó mejor desempeño en {metric_name} (menor valor)."
        elif xgb_value > baseline_value:
            return f"La regresión logística baseline presentó mejor desempeño en {metric_name} (menor valor)."
        return f"Ambos modelos presentaron el mismo valor en {metric_name}."


def main():
    args = parse_args()

    comparison_path = MODEL_DIR / "baseline_vs_xgboost_comparison.csv"
    output_path = MODEL_DIR / "baseline_vs_xgboost_summary.txt"

    if not comparison_path.exists():
        raise FileNotFoundError(
            "No existe el archivo comparativo. Ejecuta primero: "
            "python -m scripts.compare_baseline_vs_xgboost"
        )

    df = pd.read_csv(comparison_path)

    baseline = df[df["model"] == "baseline_logreg"].iloc[0].to_dict()
    xgb = df[df["model"] == args.xgb_prefix].iloc[0].to_dict()

    lines = []
    lines.append("Comparación académica entre regresión logística baseline y XGBoost")
    lines.append("=" * 80)
    lines.append("")
    lines.append(
        f"Se compararon dos enfoques de modelado para la estimación de probabilidad de clic: "
        f"una regresión logística baseline y un modelo XGBoost identificado como '{args.xgb_prefix}'."
    )
    lines.append("")
    lines.append("Resultados cuantitativos:")
    lines.append(f"- Baseline - Accuracy: {baseline.get('accuracy')}")
    lines.append(f"- Baseline - Precision: {baseline.get('precision')}")
    lines.append(f"- Baseline - Recall: {baseline.get('recall')}")
    lines.append(f"- Baseline - F1: {baseline.get('f1')}")
    lines.append(f"- Baseline - ROC-AUC: {baseline.get('roc_auc')}")
    lines.append(f"- Baseline - Brier score: {baseline.get('brier_score')}")
    lines.append("")
    lines.append(f"- XGBoost - Accuracy: {xgb.get('accuracy')}")
    lines.append(f"- XGBoost - Precision: {xgb.get('precision')}")
    lines.append(f"- XGBoost - Recall: {xgb.get('recall')}")
    lines.append(f"- XGBoost - F1: {xgb.get('f1')}")
    lines.append(f"- XGBoost - ROC-AUC: {xgb.get('roc_auc')}")
    lines.append(f"- XGBoost - Brier score: {xgb.get('brier_score')}")
    lines.append("")

    lines.append(best_model_text("accuracy", baseline.get("accuracy"), xgb.get("accuracy"), higher_is_better=True))
    lines.append(best_model_text("precision", baseline.get("precision"), xgb.get("precision"), higher_is_better=True))
    lines.append(best_model_text("recall", baseline.get("recall"), xgb.get("recall"), higher_is_better=True))
    lines.append(best_model_text("F1", baseline.get("f1"), xgb.get("f1"), higher_is_better=True))
    lines.append(best_model_text("ROC-AUC", baseline.get("roc_auc"), xgb.get("roc_auc"), higher_is_better=True))
    lines.append(best_model_text("Brier score", baseline.get("brier_score"), xgb.get("brier_score"), higher_is_better=False))
    lines.append("")
    lines.append(
        "Interpretación sugerida: la regresión logística baseline ofrece mayor interpretabilidad "
        "por medio de coeficientes directos y una lectura más simple de la contribución de cada variable. "
        "Por su parte, XGBoost puede capturar relaciones no lineales e interacciones más complejas "
        "entre señales del mensaje y atributos demográficos."
    )
    lines.append("")
    lines.append(
        "Desde la perspectiva metodológica, la regresión logística puede reportarse como modelo base "
        "por su transparencia, mientras que XGBoost puede presentarse como modelo complementario "
        "de mayor flexibilidad predictiva."
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen comparativo exportado en: {output_path.resolve()}")


if __name__ == "__main__":
    main()