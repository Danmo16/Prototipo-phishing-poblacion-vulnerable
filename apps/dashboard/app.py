from __future__ import annotations

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.db.session import SessionLocal
from core.domain.models import Campaign, Event, Target, Template, Segment

from scripts.artifact_utils import (
    latest_versioned_or_legacy,
    latest_model_run_prefix,
)


st.set_page_config(
    page_title="Phishing Prototype Dashboard",
    page_icon="📊",
    layout="wide",
)

EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")


# =========================
# Utilidades generales
# =========================

def get_db() -> Session:
    return SessionLocal()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def extract_signal(signals: dict | None, key: str) -> int:
    if not signals:
        return 0
    value = signals.get(key, 0)
    return 1 if value in [1, True, "1", "true", "True"] else 0


# =========================
# Carga de resultados - Regresión logística baseline
# =========================

def load_baseline_metrics(prefix: str = "baseline_logreg") -> dict | None:
    metrics_path = MODEL_DIR / f"{prefix}_metrics.json"
    if not metrics_path.exists():
        return None
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_baseline_coefficients_df(prefix: str = "baseline_logreg") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_coefficients.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_baseline_predictions_df(prefix: str = "baseline_logreg") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_baseline_calibration_df(prefix: str = "baseline_logreg") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_calibration.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_baseline_lift_df(prefix: str = "baseline_logreg") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_lift.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# =========================
# Carga de resultados - Comparación de modelos
# =========================

def load_model_comparison_df() -> pd.DataFrame:
    path = MODEL_DIR / "model_comparison_metrics.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_logreg_coefficients_comparison_df() -> pd.DataFrame:
    path = MODEL_DIR / "logreg_coefficients.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_tree_importances_df() -> pd.DataFrame:
    path = MODEL_DIR / "decision_tree_importances.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_model_predictions_comparison_df() -> pd.DataFrame:
    path = MODEL_DIR / "model_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# =========================
# Carga de resultados - XGBoost parametrizable
# =========================

def load_xgboost_metrics(prefix: str = "xgboost") -> dict | None:
    metrics_path = MODEL_DIR / f"{prefix}_metrics.json"
    if not metrics_path.exists():
        return None
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_xgboost_importances_df(prefix: str = "xgboost") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_feature_importances.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_xgboost_predictions_df(prefix: str = "xgboost") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_xgboost_calibration_df(prefix: str = "xgboost") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_calibration.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_xgboost_lift_df(prefix: str = "xgboost") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_lift.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# =========================
# Métricas operativas desde BD
# =========================

def load_metrics(db: Session) -> dict:
    total_campaigns = db.query(func.count(Campaign.id)).scalar() or 0
    total_targets = db.query(func.count(Target.id)).scalar() or 0
    total_templates = db.query(func.count(Template.id)).scalar() or 0
    total_segments = db.query(func.count(Segment.id)).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0

    total_delivered = (
        db.query(func.count(Event.id))
        .filter(Event.event_type == "delivered")
        .scalar()
        or 0
    )
    total_opened = (
        db.query(func.count(Event.id))
        .filter(Event.event_type == "opened")
        .scalar()
        or 0
    )
    total_clicked = (
        db.query(func.count(Event.id))
        .filter(Event.event_type == "clicked")
        .scalar()
        or 0
    )
    total_reported = (
        db.query(func.count(Event.id))
        .filter(Event.event_type == "reported")
        .scalar()
        or 0
    )

    return {
        "campaigns": total_campaigns,
        "targets": total_targets,
        "templates": total_templates,
        "segments": total_segments,
        "events": total_events,
        "delivered": total_delivered,
        "opened": total_opened,
        "clicked": total_clicked,
        "reported": total_reported,
        "open_rate": safe_rate(total_opened, total_delivered),
        "click_rate": safe_rate(total_clicked, total_delivered),
        "report_rate": safe_rate(total_reported, total_delivered),
    }


# =========================
# Dataset observado desde BD
# =========================

def load_analytic_dataset_from_db(db: Session) -> pd.DataFrame:
    campaigns = db.query(Campaign).all()
    rows = []

    for campaign in campaigns:
        template = db.query(Template).get(campaign.template_id)
        segment = db.query(Segment).get(campaign.segment_id)
        targets = db.query(Target).filter(Target.segment_id == campaign.segment_id).all()

        for target in targets:
            delivered = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "delivered",
                )
                .scalar()
                or 0
            )
            opened = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "opened",
                )
                .scalar()
                or 0
            )
            clicked = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "clicked",
                )
                .scalar()
                or 0
            )
            reported = (
                db.query(func.count(Event.id))
                .filter(
                    Event.campaign_id == campaign.id,
                    Event.target_id == target.id,
                    Event.event_type == "reported",
                )
                .scalar()
                or 0
            )

            rows.append(
                {
                    "source": "observed",
                    "campaign_id": campaign.id,
                    "campaign_status": campaign.status,
                    "campaign_channel": campaign.channel,
                    "campaign_launched_at": campaign.launched_at,
                    "template_id": template.id if template else None,
                    "template_name": template.name if template else None,
                    "template_subject": template.subject if template else None,
                    "template_description": template.description if template else None,
                    "signal_urgency": extract_signal(template.signals if template else None, "urgencia"),
                    "signal_authority": extract_signal(template.signals if template else None, "autoridad"),
                    "signal_reward": extract_signal(template.signals if template else None, "recompensa"),
                    "signal_personalization": extract_signal(template.signals if template else None, "personalizacion"),
                    "segment_id": segment.id if segment else None,
                    "age_bracket": segment.age_bracket if segment else None,
                    "gender": segment.gender if segment else None,
                    "education": segment.education if segment else None,
                    "target_id": target.id,
                    "target_recipient": target.recipient,
                    "target_uid": target.uid,
                    "delivered": delivered,
                    "opened": opened,
                    "clicked": clicked,
                    "reported": reported,
                    "opened_flag": 1 if opened > 0 else 0,
                    "clicked_flag": 1 if clicked > 0 else 0,
                    "reported_flag": 1 if reported > 0 else 0,
                }
            )

    return pd.DataFrame(rows)


# =========================
# Lectura de datasets exportados
# =========================

def load_csv_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    if "source" not in df.columns:
        if "synthetic" in path.name:
            df["source"] = "synthetic"
        elif "combined" in path.name:
            df["source"] = "combined"
        else:
            df["source"] = "observed"

    return df


def load_selected_analytic_dataset(
    db: Session,
    dataset_option: str,
) -> pd.DataFrame:

    if dataset_option == "Observado (desde BD)":
        return load_analytic_dataset_from_db(db)

    if dataset_option == "Observado (CSV exportado)":
        path = latest_versioned_or_legacy(
            EXPORT_DIR,
            "analytic_dataset_observed_*.csv",
            "analytic_dataset.csv",
        )

        if path is None:
            return pd.DataFrame()

        return load_csv_dataset(path)

    if dataset_option == "Sintético":
        path = latest_versioned_or_legacy(
            EXPORT_DIR,
            "analytic_dataset_synthetic_*.csv",
            "analytic_dataset_synthetic.csv",
        )

        if path is None:
            return pd.DataFrame()

        return load_csv_dataset(path)

    if dataset_option == "Combinado":
        path = latest_versioned_or_legacy(
            EXPORT_DIR,
            "analytic_dataset_combined_*.csv",
            "analytic_dataset_combined.csv",
        )

        if path is None:
            return pd.DataFrame()

        return load_csv_dataset(path)

    return pd.DataFrame()


# =========================
# Tablas descriptivas
# =========================

def build_general_descriptive_df(analytic_df: pd.DataFrame) -> pd.DataFrame:
    if analytic_df.empty:
        return pd.DataFrame()

    delivered = int(analytic_df["delivered"].sum())
    opened = int(analytic_df["opened_flag"].sum())
    clicked = int(analytic_df["clicked_flag"].sum())
    reported = int(analytic_df["reported_flag"].sum()) if "reported_flag" in analytic_df.columns else 0

    rows = [
        {"indicador": "Total de observaciones", "valor": len(analytic_df)},
        {"indicador": "Total de campañas", "valor": analytic_df["campaign_id"].nunique()},
        {"indicador": "Total de targets", "valor": analytic_df["target_id"].nunique()},
        {"indicador": "Total de segmentos", "valor": analytic_df["segment_id"].nunique()},
        {"indicador": "Total de plantillas", "valor": analytic_df["template_id"].nunique()},
        {"indicador": "Correos entregados", "valor": delivered},
        {"indicador": "Aperturas registradas", "valor": opened},
        {"indicador": "Clics registrados", "valor": clicked},
        {"indicador": "Reportes registrados", "valor": reported},
        {"indicador": "Tasa de apertura (%)", "valor": safe_rate(opened, delivered)},
        {"indicador": "Tasa de clic (%)", "valor": safe_rate(clicked, delivered)},
        {"indicador": "Tasa de reporte (%)", "valor": safe_rate(reported, delivered)},
    ]
    return pd.DataFrame(rows)


def build_demographic_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    grouped = (
        df.groupby(["segment_id", "age_bracket", "gender", "education"], dropna=False)
        .agg(
            targets=("target_id", "nunique"),
            delivered=("delivered", "sum"),
            opened=("opened_flag", "sum"),
            clicked=("clicked_flag", "sum"),
            reported=("reported_flag", "sum"),
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(lambda r: safe_rate(r["opened"], r["delivered"]), axis=1)
    grouped["click_rate_pct"] = grouped.apply(lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1)
    grouped["report_rate_pct"] = grouped.apply(lambda r: safe_rate(r["reported"], r["delivered"]), axis=1)
    return grouped


def build_campaign_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    grouped = (
        df.groupby(
            ["campaign_id", "campaign_status", "campaign_channel", "template_id", "segment_id"],
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

    grouped["open_rate_pct"] = grouped.apply(lambda r: safe_rate(r["opened"], r["delivered"]), axis=1)
    grouped["click_rate_pct"] = grouped.apply(lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1)
    grouped["report_rate_pct"] = grouped.apply(lambda r: safe_rate(r["reported"], r["delivered"]), axis=1)
    return grouped

def build_baseline_vs_xgboost_df(
    baseline_metrics: dict | None,
    xgboost_metrics: dict | None,
    baseline_prefix: str,
    xgboost_prefix: str,
) -> pd.DataFrame:
    """Construye la comparación con los artefactos seleccionados en la barra lateral."""
    rows = []
    metric_keys = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "brier_score",
        "n_rows",
        "train_rows",
        "test_rows",
        "positive_cases_total",
    ]

    if baseline_metrics:
        row = {"model": baseline_prefix, "model_type": "baseline_logreg"}
        row.update({key: baseline_metrics.get(key) for key in metric_keys})
        row["dataset_path"] = baseline_metrics.get("dataset_path")
        rows.append(row)

    if xgboost_metrics:
        row = {"model": xgboost_prefix, "model_type": "xgboost"}
        row.update({key: xgboost_metrics.get(key) for key in metric_keys})
        row["dataset_path"] = xgboost_metrics.get("dataset_path")
        rows.append(row)

    return pd.DataFrame(rows)


def build_baseline_vs_xgboost_summary(comparison_df: pd.DataFrame) -> str:
    """Genera una interpretación breve y advierte si la comparación no es equivalente."""
    if comparison_df.empty or len(comparison_df) < 2:
        return ""

    baseline = comparison_df.iloc[0]
    xgboost = comparison_df.iloc[1]
    lines = [
        "Comparación dinámica entre regresión logística baseline y XGBoost",
        "=" * 64,
        "",
    ]

    same_rows = baseline.get("n_rows") == xgboost.get("n_rows")
    same_train = baseline.get("train_rows") == xgboost.get("train_rows")
    same_test = baseline.get("test_rows") == xgboost.get("test_rows")

    if same_rows and same_train and same_test:
        lines.append(
            "Los dos modelos reportan el mismo número de filas y la misma distribución "
            "de entrenamiento/prueba. Esto permite una comparación más consistente, "
            "siempre que ambos scripts hayan utilizado la misma semilla y los mismos índices."
        )
    else:
        lines.append(
            "ADVERTENCIA: los modelos no reportan el mismo tamaño de dataset o la misma "
            "división de entrenamiento/prueba. La comparación es descriptiva y no debe "
            "presentarse como un contraste experimental equivalente."
        )

    lines.append("")
    for metric in ["accuracy", "precision", "recall", "f1", "roc_auc", "brier_score"]:
        baseline_value = baseline.get(metric)
        xgboost_value = xgboost.get(metric)
        lines.append(
            f"- {metric}: baseline={baseline_value} | XGBoost={xgboost_value}"
        )

    if pd.notna(baseline.get("brier_score")) and pd.notna(xgboost.get("brier_score")):
        better_brier = (
            baseline.get("model")
            if baseline.get("brier_score") < xgboost.get("brier_score")
            else xgboost.get("model")
        )
        lines.extend([
            "",
            f"El menor Brier score corresponde a {better_brier}; en esta métrica, un valor menor es mejor.",
        ])

    return "\n".join(lines)

def load_glmm_metrics(prefix: str = "glmm_clicked_segment") -> dict | None:
    path = MODEL_DIR / f"{prefix}_metrics.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_glmm_fixed_effects_df(prefix: str = "glmm_clicked_segment") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_fixed_effects.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_glmm_variance_components_df(prefix: str = "glmm_clicked_segment") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_variance_components.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_glmm_predictions_df(prefix: str = "glmm_clicked_segment") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_glmm_summary_text(prefix: str = "glmm_clicked_segment") -> str:
    path = MODEL_DIR / f"{prefix}_summary.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_glmm_academic_summary_text(prefix: str = "glmm_clicked_segment") -> str:
    path = MODEL_DIR / f"{prefix}_academic_summary.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def load_nlp_metrics(prefix: str = "nlp_distilbert_gpu") -> dict | None:
    path = MODEL_DIR / f"{prefix}_metrics.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_nlp_predictions_df(prefix: str = "nlp_distilbert_gpu") -> pd.DataFrame:
    path = MODEL_DIR / f"{prefix}_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_nlp_academic_summary_text(prefix: str = "nlp_distilbert_gpu") -> str:
    path = MODEL_DIR / f"{prefix}_academic_summary.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def build_signal_comparison_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    rows = []
    signal_labels = {
        "signal_urgency": "Urgencia",
        "signal_authority": "Autoridad",
        "signal_reward": "Recompensa",
        "signal_personalization": "Personalización",
    }

    for signal in [
        "signal_urgency",
        "signal_authority",
        "signal_reward",
        "signal_personalization",
    ]:
        with_signal = df[df[signal] == 1]
        without_signal = df[df[signal] == 0]

        rows.append(
            {
                "signal": signal_labels[signal],
                "n_with_signal": len(with_signal),
                "open_rate_with_signal_pct": safe_rate(with_signal["opened_flag"].sum(), with_signal["delivered"].sum()),
                "click_rate_with_signal_pct": safe_rate(with_signal["clicked_flag"].sum(), with_signal["delivered"].sum()),
                "report_rate_with_signal_pct": safe_rate(with_signal["reported_flag"].sum(), with_signal["delivered"].sum()),
                "n_without_signal": len(without_signal),
                "open_rate_without_signal_pct": safe_rate(without_signal["opened_flag"].sum(), without_signal["delivered"].sum()),
                "click_rate_without_signal_pct": safe_rate(without_signal["clicked_flag"].sum(), without_signal["delivered"].sum()),
                "report_rate_without_signal_pct": safe_rate(without_signal["reported_flag"].sum(), without_signal["delivered"].sum()),
            }
        )

    return pd.DataFrame(rows)


def main():
    st.title("📊 Dashboard - Prototipo de Phishing")
    st.write("Panel operativo, analítico y de modelado del prototipo académico.")

    db = get_db()

    try:
        metrics = load_metrics(db)

        st.sidebar.header("Configuración analítica")
        dataset_option = st.sidebar.selectbox(
            "Fuente del dataset analítico",
            [
                "Observado (desde BD)",
                "Observado (CSV exportado)",
                "Sintético",
                "Combinado",
            ],
            index=3,
        )

        baseline_prefix = st.sidebar.text_input(
            "Prefijo de resultados baseline",
            value="baseline_logreg_combined",
            help=(
                "Debe coincidir con el prefijo usado en --output-prefix al entrenar "
                "la regresión logística."
            ),
        )

        xgb_prefix = st.sidebar.text_input(
            "Prefijo de resultados XGBoost",
            value="xgboost_combined",
        )

        glmm_prefix = st.sidebar.text_input(
            "Prefijo de resultados GLMM",
            value="glmm_clicked_segment",
        )
        
        nlp_prefix = st.sidebar.text_input(
            "Prefijo de resultados NLP",
            value="nlp_distilbert_gpu",
        )

        baseline_run_prefix = latest_model_run_prefix(
            MODEL_DIR,
            baseline_prefix,
        )

        xgb_run_prefix = latest_model_run_prefix(
            MODEL_DIR,
            xgb_prefix,
        )

        glmm_run_prefix = latest_model_run_prefix(
            MODEL_DIR,
            glmm_prefix,
        )

        nlp_run_prefix = latest_model_run_prefix(
            MODEL_DIR,
            nlp_prefix,
        )

        analytic_df = load_selected_analytic_dataset(db, dataset_option)

        descriptive_general_df = build_general_descriptive_df(analytic_df)
        demographic_df = build_demographic_summary_df(analytic_df)
        campaign_df = build_campaign_summary_df(analytic_df)
        signal_df = build_signal_comparison_df(analytic_df)

        baseline_metrics = load_baseline_metrics(
            prefix=baseline_run_prefix
        )

        baseline_coef_df = load_baseline_coefficients_df(
            prefix=baseline_run_prefix
        )

        baseline_pred_df = load_baseline_predictions_df(
            prefix=baseline_run_prefix
        )

        baseline_calibration_df = load_baseline_calibration_df(
            prefix=baseline_run_prefix
        )

        baseline_lift_df = load_baseline_lift_df(
            prefix=baseline_run_prefix
        )

        comparison_df = load_model_comparison_df()
        comparison_logreg_coef_df = load_logreg_coefficients_comparison_df()
        tree_imp_df = load_tree_importances_df()
        comparison_pred_df = load_model_predictions_comparison_df()

        xgb_metrics = load_xgboost_metrics(prefix=xgb_run_prefix)
        xgb_importance_df = load_xgboost_importances_df(prefix=xgb_run_prefix)
        xgb_pred_df = load_xgboost_predictions_df(prefix=xgb_run_prefix)
        xgb_calibration_df = load_xgboost_calibration_df(prefix=xgb_run_prefix)
        xgb_lift_df = load_xgboost_lift_df(prefix=xgb_run_prefix)

        baseline_vs_xgb_df = build_baseline_vs_xgboost_df(
            baseline_metrics=baseline_metrics,
            xgboost_metrics=xgb_metrics,
            baseline_prefix=baseline_prefix,
            xgboost_prefix=xgb_prefix,
        )
        baseline_vs_xgb_summary = build_baseline_vs_xgboost_summary(
            baseline_vs_xgb_df
        )

        glmm_metrics = load_glmm_metrics(prefix=glmm_run_prefix)
        glmm_fixed_df = load_glmm_fixed_effects_df(prefix=glmm_run_prefix)
        glmm_vc_df = load_glmm_variance_components_df(prefix=glmm_run_prefix)
        glmm_pred_df = load_glmm_predictions_df(prefix=glmm_run_prefix)
        glmm_summary_text = load_glmm_summary_text(prefix=glmm_run_prefix)
        glmm_academic_summary_text = load_glmm_academic_summary_text(prefix=glmm_run_prefix)

        nlp_metrics = load_nlp_metrics(prefix=nlp_run_prefix)
        nlp_pred_df = load_nlp_predictions_df(prefix=nlp_run_prefix)
        nlp_academic_summary_text = load_nlp_academic_summary_text(prefix=nlp_run_prefix)

        tab1, tab2 = st.tabs(["Operativo", "Analítico"])

        with tab1:
            st.subheader("Resumen general desde base de datos")
            c1, c2, c3, c4 = st.columns(4)
            c5, c6, c7, c8 = st.columns(4)

            c1.metric("Campañas", metrics["campaigns"])
            c2.metric("Targets", metrics["targets"])
            c3.metric("Templates", metrics["templates"])
            c4.metric("Segments", metrics["segments"])
            c5.metric("Delivered", metrics["delivered"])
            c6.metric("Opened", metrics["opened"])
            c7.metric("Clicked", metrics["clicked"])
            c8.metric("Reported", metrics["reported"])

            c9, c10, c11 = st.columns(3)
            c9.metric("Open Rate", f'{metrics["open_rate"]}%')
            c10.metric("Click Rate", f'{metrics["click_rate"]}%')
            c11.metric("Report Rate", f'{metrics["report_rate"]}%')

            st.divider()
            st.subheader("Dataset analítico seleccionado")
            st.caption(f"Fuente actual: **{dataset_option}**")

            if analytic_df.empty:
                st.info("No hay datos disponibles para la fuente seleccionada.")
            else:
                st.dataframe(analytic_df, use_container_width=True)
                st.download_button(
                    "Descargar dataset analítico seleccionado (CSV)",
                    dataframe_to_csv_bytes(analytic_df),
                    "analytic_dataset_selected.csv",
                    "text/csv",
                )

                if "source" in analytic_df.columns:
                    st.markdown("#### Distribución por fuente")
                    source_counts = (
                        analytic_df["source"]
                        .value_counts(dropna=False)
                        .rename_axis("source")
                        .reset_index(name="count")
                    )
                    st.dataframe(source_counts, use_container_width=True)

        with tab2:
            st.subheader("Análisis descriptivo formal")
            st.caption(f"Calculado sobre: **{dataset_option}**")

            if descriptive_general_df.empty:
                st.info("No hay datos suficientes para el resumen descriptivo.")
            else:
                st.dataframe(descriptive_general_df, use_container_width=True)
                st.download_button(
                    "Descargar tabla descriptiva general (CSV)",
                    dataframe_to_csv_bytes(descriptive_general_df),
                    "descriptive_general_table_dashboard.csv",
                    "text/csv",
                )

            st.divider()

            st.subheader("Resumen por campaña")
            if campaign_df.empty:
                st.info("No hay datos para campañas.")
            else:
                st.dataframe(campaign_df, use_container_width=True)
                st.download_button(
                    "Descargar resumen por campaña (CSV)",
                    dataframe_to_csv_bytes(campaign_df),
                    "campaign_analytic_summary.csv",
                    "text/csv",
                )

            st.divider()

            st.subheader("Resumen demográfico")
            if demographic_df.empty:
                st.info("No hay datos demográficos para analizar.")
            else:
                st.dataframe(demographic_df, use_container_width=True)
                st.download_button(
                    "Descargar resumen demográfico (CSV)",
                    dataframe_to_csv_bytes(demographic_df),
                    "demographic_summary.csv",
                    "text/csv",
                )

            st.divider()

            st.subheader("Comparación por señales")
            if signal_df.empty:
                st.info("No hay datos de señales todavía.")
            else:
                st.dataframe(signal_df, use_container_width=True)
                st.download_button(
                    "Descargar comparación por señales (CSV)",
                    dataframe_to_csv_bytes(signal_df),
                    "signal_comparison.csv",
                    "text/csv",
                )

            st.divider()

            st.subheader("Modelo baseline - Regresión logística")
            st.caption(f"Prefijo cargado: **{baseline_prefix}**")
            if baseline_metrics is None:
                st.info(
                    "No se encontraron resultados de regresión logística para ese prefijo. "
                    "Entrena el modelo con el dataset combinado y usa el mismo valor de "
                    "--output-prefix que aparece en la barra lateral."
                )
            else:
                b1, b2, b3, b4, b5, b6 = st.columns(6)
                b1.metric("Accuracy", baseline_metrics.get("accuracy"))
                b2.metric("Precision", baseline_metrics.get("precision"))
                b3.metric("Recall", baseline_metrics.get("recall"))
                b4.metric("F1", baseline_metrics.get("f1"))
                b5.metric("ROC-AUC", baseline_metrics.get("roc_auc"))
                b6.metric("Brier", baseline_metrics.get("brier_score"))

                st.markdown("#### Coeficientes del baseline")
                if baseline_coef_df.empty:
                    st.info("No hay coeficientes cargados.")
                else:
                    st.dataframe(baseline_coef_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar coeficientes baseline (CSV)",
                        dataframe_to_csv_bytes(baseline_coef_df),
                        f"{baseline_prefix}_coefficients.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones del baseline")
                if baseline_pred_df.empty:
                    st.info("No hay predicciones cargadas.")
                else:
                    st.dataframe(baseline_pred_df, use_container_width=True)
                    st.download_button(
                        "Descargar predicciones baseline (CSV)",
                        dataframe_to_csv_bytes(baseline_pred_df),
                        f"{baseline_prefix}_predictions.csv",
                        "text/csv",
                    )

                st.markdown("#### Calibración del baseline")
                if baseline_calibration_df.empty:
                    st.info("No hay datos de calibración cargados.")
                else:
                    st.dataframe(baseline_calibration_df, use_container_width=True)
                    st.download_button(
                        "Descargar calibración baseline (CSV)",
                        dataframe_to_csv_bytes(baseline_calibration_df),
                        f"{baseline_prefix}_calibration.csv",
                        "text/csv",
                    )

                st.markdown("#### Lift del baseline")
                if baseline_lift_df.empty:
                    st.info("No hay tabla de lift cargada.")
                else:
                    st.dataframe(baseline_lift_df, use_container_width=True)
                    st.download_button(
                        "Descargar lift baseline (CSV)",
                        dataframe_to_csv_bytes(baseline_lift_df),
                        f"{baseline_prefix}_lift.csv",
                        "text/csv",
                    )

            st.divider()

            st.subheader("Modelo XGBoost")
            st.caption(f"Prefijo cargado: **{xgb_prefix}**")

            if xgb_metrics is None:
                st.info(
                    "No se encontraron resultados de XGBoost para ese prefijo. "
                    "Ejecuta el entrenamiento o ajusta el prefijo en la barra lateral."
                )
            else:
                x1, x2, x3, x4, x5, x6 = st.columns(6)
                x1.metric("Accuracy", xgb_metrics.get("accuracy"))
                x2.metric("Precision", xgb_metrics.get("precision"))
                x3.metric("Recall", xgb_metrics.get("recall"))
                x4.metric("F1", xgb_metrics.get("f1"))
                x5.metric("ROC-AUC", xgb_metrics.get("roc_auc"))
                x6.metric("Brier", xgb_metrics.get("brier_score"))

                st.markdown("#### Métricas completas XGBoost")
                st.json(xgb_metrics)

                st.markdown("#### Importancia de variables - XGBoost")
                if xgb_importance_df.empty:
                    st.info("No hay importancias cargadas.")
                else:
                    st.dataframe(xgb_importance_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar importancias XGBoost (CSV)",
                        dataframe_to_csv_bytes(xgb_importance_df),
                        f"{xgb_prefix}_feature_importances.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones - XGBoost")
                if xgb_pred_df.empty:
                    st.info("No hay predicciones cargadas.")
                else:
                    st.dataframe(xgb_pred_df, use_container_width=True)
                    st.download_button(
                        "Descargar predicciones XGBoost (CSV)",
                        dataframe_to_csv_bytes(xgb_pred_df),
                        f"{xgb_prefix}_predictions.csv",
                        "text/csv",
                    )

                st.markdown("#### Calibración - XGBoost")
                if xgb_calibration_df.empty:
                    st.info("No hay datos de calibración cargados.")
                else:
                    st.dataframe(xgb_calibration_df, use_container_width=True)
                    st.download_button(
                        "Descargar calibración XGBoost (CSV)",
                        dataframe_to_csv_bytes(xgb_calibration_df),
                        f"{xgb_prefix}_calibration.csv",
                        "text/csv",
                    )

                st.markdown("#### Lift - XGBoost")
                if xgb_lift_df.empty:
                    st.info("No hay tabla de lift cargada.")
                else:
                    st.dataframe(xgb_lift_df, use_container_width=True)
                    st.download_button(
                        "Descargar lift XGBoost (CSV)",
                        dataframe_to_csv_bytes(xgb_lift_df),
                        f"{xgb_prefix}_lift.csv",
                        "text/csv",
                    )

            st.divider()

            st.subheader("Modelo GLMM binomial")
            st.caption(f"Prefijo cargado: **{glmm_prefix}**")

            if glmm_metrics is None:
                st.info(
                    "No se encontraron resultados de GLMM para ese prefijo. Ejecuta por ejemplo:\n"
                    "python -m scripts.train_glmm_model --dataset data/exports/analytic_dataset_combined.csv "
                    "--output-prefix glmm_clicked_segment --random-effect segment_id --method vb\n"
                    "python -m scripts.summarize_glmm_results --prefix glmm_clicked_segment"
                )
            else:
                g1, g2, g3, g4 = st.columns(4)
                g1.metric("Observaciones", glmm_metrics.get("n_rows"))
                g2.metric("Casos positivos", glmm_metrics.get("positive_cases_total"))
                g3.metric("Efecto aleatorio", glmm_metrics.get("random_effect"))
                g4.metric("Método", glmm_metrics.get("method"))

                st.markdown("#### Configuración del GLMM")
                st.json(glmm_metrics)

                st.markdown("#### Efectos fijos")
                if glmm_fixed_df.empty:
                    st.info("No hay efectos fijos cargados.")
                else:
                    st.dataframe(glmm_fixed_df, use_container_width=True)
                    st.download_button(
                        "Descargar efectos fijos GLMM (CSV)",
                        dataframe_to_csv_bytes(glmm_fixed_df),
                        f"{glmm_prefix}_fixed_effects.csv",
                        "text/csv",
                    )

                st.markdown("#### Componentes de varianza")
                if glmm_vc_df.empty:
                    st.info("No hay componentes de varianza cargados.")
                else:
                    st.dataframe(glmm_vc_df, use_container_width=True)
                    st.download_button(
                        "Descargar componentes de varianza GLMM (CSV)",
                        dataframe_to_csv_bytes(glmm_vc_df),
                        f"{glmm_prefix}_variance_components.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones GLMM")
                if glmm_pred_df.empty:
                    st.info("No hay predicciones cargadas.")
                else:
                    st.dataframe(glmm_pred_df.head(100), use_container_width=True)
                    st.download_button(
                        "Descargar predicciones GLMM (CSV)",
                        dataframe_to_csv_bytes(glmm_pred_df),
                        f"{glmm_prefix}_predictions.csv",
                        "text/csv",
                    )

                st.markdown("#### Resumen técnico del ajuste")
                if glmm_summary_text:
                    st.text(glmm_summary_text)
                else:
                    st.info("No hay resumen técnico cargado.")

                st.markdown("#### Interpretación académica del GLMM")
                if glmm_academic_summary_text:
                    st.text(glmm_academic_summary_text)
                else:
                    st.info("No hay resumen académico cargado.")

            st.divider()

            st.subheader("Modelo NLP - DistilBERT")
            st.caption(f"Prefijo cargado: **{nlp_prefix}**")

            if nlp_metrics is None:
                st.info(
                    "No se encontraron resultados del modelo NLP para ese prefijo. Ejecuta por ejemplo:\n"
                    "python -m scripts.export_nlp_dataset\n"
                    "python -m scripts.train_nlp_model --output-prefix nlp_distilbert_gpu --epochs 4 --batch-size 16 --max-length 192\n"
                    "python -m scripts.summarize_nlp_results --prefix nlp_distilbert_gpu"
                )
            else:
                n1, n2, n3, n4, n5, n6 = st.columns(6)
                n1.metric("Accuracy", nlp_metrics.get("accuracy"))
                n2.metric("Precision", nlp_metrics.get("precision"))
                n3.metric("Recall", nlp_metrics.get("recall"))
                n4.metric("F1", nlp_metrics.get("f1"))
                n5.metric("ROC-AUC", nlp_metrics.get("roc_auc"))
                n6.metric("Device", nlp_metrics.get("device"))

                st.markdown("#### Configuración y métricas NLP")
                st.json(nlp_metrics)

                st.markdown("#### Predicciones NLP")
                if nlp_pred_df.empty:
                    st.info("No hay predicciones NLP cargadas.")
                else:
                    st.dataframe(nlp_pred_df.head(100), use_container_width=True)
                    st.download_button(
                        "Descargar predicciones NLP (CSV)",
                        dataframe_to_csv_bytes(nlp_pred_df),
                        f"{nlp_prefix}_predictions.csv",
                        "text/csv",
                    )

                st.markdown("#### Interpretación académica del NLP")
                if nlp_academic_summary_text:
                    st.text(nlp_academic_summary_text)
                else:
                    st.info("No hay resumen académico NLP cargado.")

            st.divider()

            st.subheader("Comparación baseline vs XGBoost")
            st.caption(
                f"Comparación cargada dinámicamente: **{baseline_prefix}** vs **{xgb_prefix}**"
            )
            if len(baseline_vs_xgb_df) < 2:
                st.info(
                    "Para construir la comparación deben existir los archivos de métricas "
                    "de ambos prefijos seleccionados."
                )
            else:
                st.dataframe(baseline_vs_xgb_df, use_container_width=True)
                st.download_button(
                    "Descargar comparación baseline vs XGBoost (CSV)",
                    dataframe_to_csv_bytes(baseline_vs_xgb_df),
                    f"{baseline_prefix}_vs_{xgb_prefix}_comparison.csv",
                    "text/csv",
                )

                if baseline_vs_xgb_summary:
                    st.markdown("#### Interpretación comparativa")
                    st.text(baseline_vs_xgb_summary)

            st.divider()

            st.subheader("Comparación de modelos")
            if comparison_df.empty:
                st.info(
                    "No se encontraron resultados de comparación de modelos. "
                    "Ejecuta: python -m scripts.compare_models"
                )
            else:
                st.dataframe(comparison_df, use_container_width=True)
                st.download_button(
                    "Descargar métricas comparativas (CSV)",
                    dataframe_to_csv_bytes(comparison_df),
                    "model_comparison_metrics.csv",
                    "text/csv",
                )

                st.markdown("#### Coeficientes logística (comparación)")
                if not comparison_logreg_coef_df.empty:
                    st.dataframe(comparison_logreg_coef_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar coeficientes logística comparación (CSV)",
                        dataframe_to_csv_bytes(comparison_logreg_coef_df),
                        "logreg_coefficients.csv",
                        "text/csv",
                    )

                st.markdown("#### Importancias árbol de decisión")
                if not tree_imp_df.empty:
                    st.dataframe(tree_imp_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar importancias árbol (CSV)",
                        dataframe_to_csv_bytes(tree_imp_df),
                        "decision_tree_importances.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones comparativas")
                if not comparison_pred_df.empty:
                    st.dataframe(comparison_pred_df, use_container_width=True)
                    st.download_button(
                        "Descargar predicciones comparativas (CSV)",
                        dataframe_to_csv_bytes(comparison_pred_df),
                        "model_predictions.csv",
                        "text/csv",
                    )

            st.divider()

            st.subheader("Interpretación académica")
            st.write(
                "Esta sección permite alternar entre datos observados, sintéticos y combinados. "
                "Además, integra resultados de análisis descriptivo, regresión logística baseline, "
                "XGBoost, GLMM y un componente NLP basado en transformers. "
                "De esta forma, el prototipo combina variables estructuradas, heterogeneidad por grupos "
                "y representación semántica del contenido textual de los mensajes."
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()