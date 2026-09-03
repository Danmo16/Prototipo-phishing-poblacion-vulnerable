# scripts/generate_analytic_html_report.py
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from scripts.artifact_utils import (
    build_timestamp,
    build_artifact_name,
)


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def df_to_html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "<p><em>No hay datos disponibles.</em></p>"
    return df.head(max_rows).to_html(index=False, border=0, classes="report-table")


def metric_card(title: str, value) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """


def build_html() -> str:
    general_df = load_csv(EXPORT_DIR / "descriptive_general_table.csv")
    campaign_df = load_csv(EXPORT_DIR / "descriptive_campaign_table.csv")
    segment_df = load_csv(EXPORT_DIR / "descriptive_segment_table.csv")
    signal_df = load_csv(EXPORT_DIR / "descriptive_signal_table.csv")
    conclusions_path = EXPORT_DIR / "descriptive_conclusions.txt"
    conclusions_text = conclusions_path.read_text(encoding="utf-8") if conclusions_path.exists() else "No disponible."

    baseline_metrics = load_json(MODEL_DIR / "baseline_logreg_metrics.json")
    baseline_coef_df = load_csv(MODEL_DIR / "baseline_logreg_coefficients.csv")
    baseline_calibration_df = load_csv(MODEL_DIR / "baseline_logreg_calibration.csv")
    baseline_lift_df = load_csv(MODEL_DIR / "baseline_logreg_lift.csv")

    xgb_metrics = load_json(MODEL_DIR / "xgboost_combined_metrics.json")
    xgb_importance_df = load_csv(MODEL_DIR / "xgboost_combined_feature_importances.csv")
    xgb_calibration_df = load_csv(MODEL_DIR / "xgboost_combined_calibration.csv")
    xgb_lift_df = load_csv(MODEL_DIR / "xgboost_combined_lift.csv")

    comparison_df = load_csv(MODEL_DIR / "baseline_vs_xgboost_comparison.csv")
    comparison_summary_path = MODEL_DIR / "baseline_vs_xgboost_summary.txt"
    comparison_summary = comparison_summary_path.read_text(encoding="utf-8") if comparison_summary_path.exists() else "No disponible."

    baseline_cards = ""
    if baseline_metrics:
        baseline_cards = "".join(
            [
                metric_card("Accuracy", baseline_metrics.get("accuracy")),
                metric_card("Precision", baseline_metrics.get("precision")),
                metric_card("Recall", baseline_metrics.get("recall")),
                metric_card("F1", baseline_metrics.get("f1")),
                metric_card("ROC-AUC", baseline_metrics.get("roc_auc")),
                metric_card("Brier", baseline_metrics.get("brier_score")),
            ]
        )

    xgb_cards = ""
    if xgb_metrics:
        xgb_cards = "".join(
            [
                metric_card("Accuracy", xgb_metrics.get("accuracy")),
                metric_card("Precision", xgb_metrics.get("precision")),
                metric_card("Recall", xgb_metrics.get("recall")),
                metric_card("F1", xgb_metrics.get("f1")),
                metric_card("ROC-AUC", xgb_metrics.get("roc_auc")),
                metric_card("Brier", xgb_metrics.get("brier_score")),
            ]
        )

    html = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Reporte Analítico - Prototipo de Phishing</title>
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                margin: 40px;
                color: #1f2937;
                background: #ffffff;
            }}
            h1, h2, h3 {{
                color: #111827;
            }}
            h1 {{
                border-bottom: 3px solid #2563eb;
                padding-bottom: 10px;
            }}
            .section {{
                margin-top: 36px;
            }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(180px, 1fr));
                gap: 16px;
                margin: 20px 0;
            }}
            .metric-card {{
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 16px;
                background: #f9fafb;
            }}
            .metric-title {{
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 8px;
            }}
            .metric-value {{
                font-size: 22px;
                font-weight: bold;
                color: #111827;
            }}
            .report-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
                font-size: 14px;
            }}
            .report-table th, .report-table td {{
                border: 1px solid #d1d5db;
                padding: 8px;
                text-align: left;
            }}
            .report-table th {{
                background: #f3f4f6;
            }}
            .note {{
                background: #eff6ff;
                border-left: 4px solid #2563eb;
                padding: 12px;
                margin: 16px 0;
            }}
            .mono {{
                white-space: pre-wrap;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                padding: 16px;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        <h1>Reporte Analítico del Prototipo de Simulación de Phishing</h1>

        <div class="note">
            Este reporte consolida resultados descriptivos, métricas de modelado y comparación entre enfoques
            predictivos desarrollados para el trabajo de grado.
        </div>

        <div class="section">
            <h2>1. Resumen descriptivo general</h2>
            {df_to_html_table(general_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>2. Resultados por campaña</h2>
            {df_to_html_table(campaign_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>3. Resultados demográficos</h2>
            {df_to_html_table(segment_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>4. Comparación por señales</h2>
            {df_to_html_table(signal_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>5. Conclusiones descriptivas automáticas</h2>
            <div class="mono">{conclusions_text}</div>
        </div>

        <div class="section">
            <h2>6. Modelo baseline - Regresión logística</h2>
            <div class="metric-grid">
                {baseline_cards if baseline_cards else "<p><em>No hay métricas del baseline.</em></p>"}
            </div>
            <h3>6.1 Coeficientes principales</h3>
            {df_to_html_table(baseline_coef_df, max_rows=15)}
            <h3>6.2 Calibración</h3>
            {df_to_html_table(baseline_calibration_df, max_rows=20)}
            <h3>6.3 Lift</h3>
            {df_to_html_table(baseline_lift_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>7. Modelo XGBoost</h2>
            <div class="metric-grid">
                {xgb_cards if xgb_cards else "<p><em>No hay métricas de XGBoost.</em></p>"}
            </div>
            <h3>7.1 Importancia de variables</h3>
            {df_to_html_table(xgb_importance_df, max_rows=15)}
            <h3>7.2 Calibración</h3>
            {df_to_html_table(xgb_calibration_df, max_rows=20)}
            <h3>7.3 Lift</h3>
            {df_to_html_table(xgb_lift_df, max_rows=20)}
        </div>

        <div class="section">
            <h2>8. Comparación baseline vs XGBoost</h2>
            {df_to_html_table(comparison_df, max_rows=10)}
            <h3>8.1 Interpretación comparativa</h3>
            <div class="mono">{comparison_summary}</div>
        </div>

        <div class="section">
            <h2>9. Interpretación general</h2>
            <p>
                El reporte integra evidencia descriptiva y predictiva sobre la interacción de usuarios
                con campañas simuladas de phishing. Desde la perspectiva metodológica, la regresión logística
                aporta interpretabilidad y transparencia, mientras que XGBoost aporta flexibilidad para modelar
                relaciones más complejas entre señales del mensaje y atributos demográficos.
            </p>
            <p>
                La inclusión de Brier score, calibración y lift fortalece la evaluación probabilística del modelo
                y permite una lectura más madura del comportamiento predictivo del prototipo.
            </p>
        </div>
    </body>
    </html>
    """
    return html


def main():
    html = build_html()

    timestamp = build_timestamp()

    output_path = REPORT_DIR / build_artifact_name(
        artifact="analytic_report",
        timestamp=timestamp,
        extension="html",
    )

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    print(f"Reporte HTML exportado en: {output_path.resolve()}")


if __name__ == "__main__":
    main()