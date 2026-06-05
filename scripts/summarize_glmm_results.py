# scripts/summarize_glmm_results.py
from __future__ import annotations

import json
import argparse
from pathlib import Path
import pandas as pd


MODEL_DIR = Path("data/models")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un resumen académico del GLMM."
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="glmm_clicked",
        help="Prefijo del GLMM exportado.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    metrics_path = MODEL_DIR / f"{args.prefix}_metrics.json"
    fixed_path = MODEL_DIR / f"{args.prefix}_fixed_effects.csv"
    vc_path = MODEL_DIR / f"{args.prefix}_variance_components.csv"
    output_path = MODEL_DIR / f"{args.prefix}_academic_summary.txt"

    if not metrics_path.exists() or not fixed_path.exists() or not vc_path.exists():
        raise FileNotFoundError(
            f"Faltan artefactos del GLMM con prefijo '{args.prefix}'. "
            f"Ejecuta primero: python -m scripts.train_glmm_model --output-prefix {args.prefix}"
        )

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    fixed_df = pd.read_csv(fixed_path).sort_values("posterior_mean", ascending=False)
    vc_df = pd.read_csv(vc_path)

    top_positive = fixed_df.head(5)
    top_negative = fixed_df.sort_values("posterior_mean", ascending=True).head(5)

    lines = []
    lines.append("Resumen académico del GLMM binomial")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Dataset utilizado: {metrics.get('dataset_path')}")
    lines.append(f"Efecto aleatorio: {metrics.get('random_effect')}")
    lines.append(f"Método de ajuste: {metrics.get('method')}")
    lines.append(f"Observaciones totales: {metrics.get('n_rows')}")
    lines.append(f"Casos positivos totales: {metrics.get('positive_cases_total')}")
    lines.append("")
    lines.append("Interpretación general:")
    lines.append(
        "El modelo GLMM binomial se utilizó como aproximación para analizar la probabilidad "
        "de clic incorporando efectos fijos de señales del mensaje y variables demográficas, "
        "junto con un intercepto aleatorio por grupo."
    )
    lines.append("")

    lines.append("Términos con mayor asociación positiva estimada:")
    for _, row in top_positive.iterrows():
        lines.append(
            f"- {row['term']}: media posterior={row['posterior_mean']:.6f}, "
            f"OR aprox={row['odds_ratio_approx']:.6f}"
        )

    lines.append("")
    lines.append("Términos con asociación negativa estimada:")
    for _, row in top_negative.iterrows():
        lines.append(
            f"- {row['term']}: media posterior={row['posterior_mean']:.6f}, "
            f"OR aprox={row['odds_ratio_approx']:.6f}"
        )

    lines.append("")
    lines.append("Componentes de varianza aleatoria:")
    for _, row in vc_df.iterrows():
        lines.append(
            f"- {row['component']}: log(sd)={row['posterior_mean_log_sd']:.6f}, "
            f"sd aprox={row['sd_approx']:.6f}"
        )

    lines.append("")
    lines.append(
        "Interpretación sugerida: este análisis permite aproximar la existencia de heterogeneidad "
        "entre grupos (por ejemplo, segmentos o campañas) más allá de los efectos fijos observados. "
        "Dado el carácter exploratorio del estudio y la mezcla de datos observados y sintéticos, "
        "los resultados del GLMM deben interpretarse como evidencia complementaria y no confirmatoria."
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen académico exportado en: {output_path.resolve()}")


if __name__ == "__main__":
    main()