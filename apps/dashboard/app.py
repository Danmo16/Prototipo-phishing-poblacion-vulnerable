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

def load_baseline_metrics() -> dict | None:
    metrics_path = MODEL_DIR / "baseline_logreg_metrics.json"
    if not metrics_path.exists():
        return None

    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_baseline_coefficients_df() -> pd.DataFrame:
    path = MODEL_DIR / "baseline_logreg_coefficients.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_baseline_predictions_df() -> pd.DataFrame:
    path = MODEL_DIR / "baseline_logreg_predictions.csv"
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

    return {
        "campaigns": total_campaigns,
        "targets": total_targets,
        "templates": total_templates,
        "segments": total_segments,
        "events": total_events,
        "delivered": total_delivered,
        "opened": total_opened,
        "clicked": total_clicked,
        "open_rate": safe_rate(total_opened, total_delivered),
        "click_rate": safe_rate(total_clicked, total_delivered),
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
                    "opened_flag": 1 if opened > 0 else 0,
                    "clicked_flag": 1 if clicked > 0 else 0,
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


def load_selected_analytic_dataset(db: Session, dataset_option: str) -> pd.DataFrame:
    if dataset_option == "Observado (desde BD)":
        return load_analytic_dataset_from_db(db)

    if dataset_option == "Observado (CSV exportado)":
        return load_csv_dataset(EXPORT_DIR / "analytic_dataset.csv")

    if dataset_option == "Sintético":
        return load_csv_dataset(EXPORT_DIR / "analytic_dataset_synthetic.csv")

    if dataset_option == "Combinado":
        return load_csv_dataset(EXPORT_DIR / "analytic_dataset_combined.csv")

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

    rows = [
        {"indicador": "Total de observaciones", "valor": len(analytic_df)},
        {"indicador": "Total de campañas", "valor": analytic_df["campaign_id"].nunique()},
        {"indicador": "Total de targets", "valor": analytic_df["target_id"].nunique()},
        {"indicador": "Total de segmentos", "valor": analytic_df["segment_id"].nunique()},
        {"indicador": "Total de plantillas", "valor": analytic_df["template_id"].nunique()},
        {"indicador": "Correos entregados", "valor": delivered},
        {"indicador": "Aperturas registradas", "valor": opened},
        {"indicador": "Clics registrados", "valor": clicked},
        {"indicador": "Tasa de apertura (%)", "valor": safe_rate(opened, delivered)},
        {"indicador": "Tasa de clic (%)", "valor": safe_rate(clicked, delivered)},
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
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["click_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
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
        )
        .reset_index()
    )

    grouped["open_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["opened"], r["delivered"]), axis=1
    )
    grouped["click_rate_pct"] = grouped.apply(
        lambda r: safe_rate(r["clicked"], r["delivered"]), axis=1
    )
    return grouped


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
                "open_rate_with_signal_pct": safe_rate(
                    with_signal["opened_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "click_rate_with_signal_pct": safe_rate(
                    with_signal["clicked_flag"].sum(),
                    with_signal["delivered"].sum(),
                ),
                "n_without_signal": len(without_signal),
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

        xgb_prefix = st.sidebar.text_input(
            "Prefijo de resultados XGBoost",
            value="xgboost",
        )

        analytic_df = load_selected_analytic_dataset(db, dataset_option)

        descriptive_general_df = build_general_descriptive_df(analytic_df)
        demographic_df = build_demographic_summary_df(analytic_df)
        campaign_df = build_campaign_summary_df(analytic_df)
        signal_df = build_signal_comparison_df(analytic_df)

        baseline_metrics = load_baseline_metrics()
        baseline_coef_df = load_baseline_coefficients_df()
        baseline_pred_df = load_baseline_predictions_df()

        comparison_df = load_model_comparison_df()
        comparison_logreg_coef_df = load_logreg_coefficients_comparison_df()
        tree_imp_df = load_tree_importances_df()
        comparison_pred_df = load_model_predictions_comparison_df()

        xgb_metrics = load_xgboost_metrics(prefix=xgb_prefix)
        xgb_importance_df = load_xgboost_importances_df(prefix=xgb_prefix)
        xgb_pred_df = load_xgboost_predictions_df(prefix=xgb_prefix)

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
            c8.metric("Open / Click Rate", f'{metrics["open_rate"]}% / {metrics["click_rate"]}%')

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
            if baseline_metrics is None:
                st.info(
                    "No se encontraron resultados de regresión logística baseline. "
                    "Ejecuta: python -m scripts.train_baseline_model"
                )
            else:
                b1, b2, b3, b4, b5 = st.columns(5)
                b1.metric("Accuracy", baseline_metrics.get("accuracy"))
                b2.metric("Precision", baseline_metrics.get("precision"))
                b3.metric("Recall", baseline_metrics.get("recall"))
                b4.metric("F1", baseline_metrics.get("f1"))
                b5.metric("ROC-AUC", baseline_metrics.get("roc_auc"))

                st.markdown("#### Coeficientes del baseline")
                if baseline_coef_df.empty:
                    st.info("No hay coeficientes cargados.")
                else:
                    st.dataframe(baseline_coef_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar coeficientes baseline (CSV)",
                        dataframe_to_csv_bytes(baseline_coef_df),
                        "baseline_logreg_coefficients.csv",
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
                        "baseline_logreg_predictions.csv",
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
                x1, x2, x3, x4, x5 = st.columns(5)
                x1.metric("Accuracy", xgb_metrics.get("accuracy"))
                x2.metric("Precision", xgb_metrics.get("precision"))
                x3.metric("Recall", xgb_metrics.get("recall"))
                x4.metric("F1", xgb_metrics.get("f1"))
                x5.metric("ROC-AUC", xgb_metrics.get("roc_auc"))

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
                "XGBoost y comparación entre modelos, manteniendo trazabilidad metodológica para la tesis."
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()