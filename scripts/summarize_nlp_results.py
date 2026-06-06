# scripts/summarize_nlp_results.py
from __future__ import annotations

import json
import argparse
from pathlib import Path


MODEL_DIR = Path("data/models")


def parse_args():
    parser = argparse.ArgumentParser(description="Genera resumen académico del modelo NLP.")
    parser.add_argument("--prefix", type=str, default="nlp_distilbert")
    return parser.parse_args()


def main():
    args = parse_args()

    metrics_path = MODEL_DIR / f"{args.prefix}_metrics.json"
    output_path = MODEL_DIR / f"{args.prefix}_academic_summary.txt"

    if not metrics_path.exists():
        raise FileNotFoundError(
            f"No existe {metrics_path}. Ejecuta primero: python -m scripts.train_nlp_model --output-prefix {args.prefix}"
        )

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    lines = []
    lines.append("Resumen académico del modelo NLP")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Modelo base: {metrics.get('model_name')}")
    lines.append(f"Dataset utilizado: {metrics.get('dataset_path')}")
    lines.append(f"Observaciones totales: {metrics.get('n_rows')}")
    lines.append(f"Observaciones de entrenamiento: {metrics.get('train_rows')}")
    lines.append(f"Observaciones de prueba: {metrics.get('test_rows')}")
    lines.append(f"Casos positivos totales: {metrics.get('positive_cases_total')}")
    lines.append(f"Accuracy: {metrics.get('accuracy')}")
    lines.append(f"Precision: {metrics.get('precision')}")
    lines.append(f"Recall: {metrics.get('recall')}")
    lines.append(f"F1-score: {metrics.get('f1')}")
    lines.append(f"ROC-AUC: {metrics.get('roc_auc')}")
    lines.append("")
    lines.append(
        "Interpretación sugerida: el componente NLP introduce una representación semántica "
        "del contenido textual del mensaje, permitiendo complementar el análisis basado en "
        "señales estructuradas y variables demográficas."
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen académico exportado en: {output_path.resolve()}")


if __name__ == "__main__":
    main()