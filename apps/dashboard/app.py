from __future__ import annotations

import sys
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


def get_db() -> Session:
    return SessionLocal()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

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

def load_model_comparison_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    path = model_dir / "model_comparison_metrics.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_logreg_coefficients_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    path = model_dir / "logreg_coefficients.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_tree_importances_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    path = model_dir / "decision_tree_importances.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_model_predictions_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    path = model_dir / "model_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def load_model_metrics() -> dict | None:
    model_dir = Path("data/models")
    metrics_path = model_dir / "baseline_logreg_metrics.json"
    if not metrics_path.exists():
        return None

    import json
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_model_coefficients_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    coef_path = model_dir / "baseline_logreg_coefficients.csv"
    if not coef_path.exists():
        return pd.DataFrame()
    return pd.read_csv(coef_path)


def load_model_predictions_df() -> pd.DataFrame:
    model_dir = Path("data/models")
    pred_path = model_dir / "baseline_logreg_predictions.csv"
    if not pred_path.exists():
        return pd.DataFrame()
    return pd.read_csv(pred_path)


def extract_signal(signals: dict | None, key: str) -> int:
    if not signals:
        return 0
    value = signals.get(key, 0)
    return 1 if value in [1, True, "1", "true", "True"] else 0


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


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


def load_analytic_dataset_df(db: Session) -> pd.DataFrame:
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
                    "campaign_id": campaign.id,
                    "campaign_status": campaign.status,
                    "campaign_channel": campaign.channel,
                    "template_id": template.id if template else None,
                    "template_name": template.name if template else None,
                    "template_subject": template.subject if template else None,
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


def build_signal_comparison_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    rows = []
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
                "signal": signal,
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
        df.groupby(["campaign_id", "campaign_status", "campaign_channel", "template_id", "segment_id"], dropna=False)
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


def main():
    st.title("📊 Dashboard - Prototipo de Phishing")
    st.write("Panel operativo y analítico del prototipo académico.")

    db = get_db()

    try:
        metrics = load_metrics(db)
        analytic_df = load_analytic_dataset_df(db)
        signal_df = build_signal_comparison_df(analytic_df)
        demographic_df = build_demographic_summary_df(analytic_df)
        campaign_df = build_campaign_summary_df(analytic_df)
        model_metrics = load_model_metrics()
        model_coef_df = load_model_coefficients_df()
        model_pred_df = load_model_predictions_df()
        model_comparison_df = load_model_comparison_df()
        logreg_coef_df = load_logreg_coefficients_df()
        tree_imp_df = load_tree_importances_df()
        model_pred_df = load_model_predictions_df()
        descriptive_general_df = build_general_descriptive_df(analytic_df)

        tab1, tab2 = st.tabs(["Operativo", "Analítico"])

        with tab1:
            st.subheader("Resumen general")
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
            st.subheader("Dataset analítico")
            if analytic_df.empty:
                st.info("No hay datos analíticos todavía.")
            else:
                st.dataframe(analytic_df, use_container_width=True)
                st.download_button(
                    "Descargar dataset analítico (CSV)",
                    dataframe_to_csv_bytes(analytic_df),
                    "analytic_dataset_dashboard.csv",
                    "text/csv",
                )

        with tab2:

            st.subheader("Análisis descriptivo formal")
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

                st.markdown("#### Comentario interpretativo")
                delivered_val = descriptive_general_df.loc[
                    descriptive_general_df["indicador"] == "Correos entregados", "valor"
                ].iloc[0]
                opened_val = descriptive_general_df.loc[
                    descriptive_general_df["indicador"] == "Aperturas registradas", "valor"
                ].iloc[0]
                clicked_val = descriptive_general_df.loc[
                    descriptive_general_df["indicador"] == "Clics registrados", "valor"
                ].iloc[0]
                open_rate_val = descriptive_general_df.loc[
                    descriptive_general_df["indicador"] == "Tasa de apertura (%)", "valor"
                ].iloc[0]
                click_rate_val = descriptive_general_df.loc[
                    descriptive_general_df["indicador"] == "Tasa de clic (%)", "valor"
                ].iloc[0]

                st.write(
                    f"En este corte se observaron {delivered_val} entregas, "
                    f"{opened_val} aperturas y {clicked_val} clics. "
                    f"La tasa de apertura fue de {open_rate_val}% y la tasa de clic fue de "
                    f"{click_rate_val}%, lo que permite caracterizar preliminarmente "
                    f"la respuesta de los usuarios ante las campañas simuladas."
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

                d1, d2 = st.columns(2)
                with d1:
                    st.caption("Tasa de apertura por segmento (%)")
                    st.bar_chart(demographic_df.set_index("segment_id")[["open_rate_pct"]])
                with d2:
                    st.caption("Tasa de clic por segmento (%)")
                    st.bar_chart(demographic_df.set_index("segment_id")[["click_rate_pct"]])

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

                s1, s2 = st.columns(2)
                with s1:
                    st.caption("Open rate con señal activa (%)")
                    st.bar_chart(signal_df.set_index("signal")[["open_rate_with_signal_pct"]])
                with s2:
                    st.caption("Click rate con señal activa (%)")
                    st.bar_chart(signal_df.set_index("signal")[["click_rate_with_signal_pct"]])

            st.divider()

            st.subheader("Interpretación académica")
            st.write(
                "Esta sección permite contrastar la respuesta de los usuarios según "
                "las señales de las plantillas y según su segmento demográfico. "
                "Estos resultados sirven como base para sustentar la identificación "
                "de población vulnerable y la influencia de los disparadores del mensaje."
            )

            st.divider()
            st.subheader("Modelo baseline - Regresión logística")

            if model_metrics is None:
                st.info(
                    "Aún no hay resultados de modelo. Ejecuta:\n"
                    "python -m scripts.train_baseline_model"
                )
            else:
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Accuracy", model_metrics.get("accuracy"))
                m2.metric("Precision", model_metrics.get("precision"))
                m3.metric("Recall", model_metrics.get("recall"))
                m4.metric("F1", model_metrics.get("f1"))
                m5.metric("ROC-AUC", model_metrics.get("roc_auc"))

                st.markdown("#### Variables más influyentes")
                if model_coef_df.empty:
                    st.info("No hay coeficientes cargados.")
                else:
                    st.dataframe(model_coef_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar coeficientes del modelo (CSV)",
                        dataframe_to_csv_bytes(model_coef_df),
                        "baseline_logreg_coefficients.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones del modelo")
                if model_pred_df.empty:
                    st.info("No hay predicciones cargadas.")
                else:
                    st.dataframe(model_pred_df, use_container_width=True)
                    st.download_button(
                        "Descargar predicciones del modelo (CSV)",
                        dataframe_to_csv_bytes(model_pred_df),
                        "baseline_logreg_predictions.csv",
                        "text/csv",
                    )

            st.divider()
            st.subheader("Comparación de modelos")

            if model_comparison_df.empty:
                st.info(
                    "Aún no hay comparación de modelos. Ejecuta:\n"
                    "python -m scripts.compare_models"
                )
            else:
                st.dataframe(model_comparison_df, use_container_width=True)
                st.download_button(
                    "Descargar métricas comparativas (CSV)",
                    dataframe_to_csv_bytes(model_comparison_df),
                    "model_comparison_metrics.csv",
                    "text/csv",
                )

                st.markdown("#### Coeficientes - Regresión Logística")
                if not logreg_coef_df.empty:
                    st.dataframe(logreg_coef_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar coeficientes logística (CSV)",
                        dataframe_to_csv_bytes(logreg_coef_df),
                        "logreg_coefficients.csv",
                        "text/csv",
                    )

                st.markdown("#### Importancias - Árbol de decisión")
                if not tree_imp_df.empty:
                    st.dataframe(tree_imp_df.head(20), use_container_width=True)
                    st.download_button(
                        "Descargar importancias árbol (CSV)",
                        dataframe_to_csv_bytes(tree_imp_df),
                        "decision_tree_importances.csv",
                        "text/csv",
                    )

                st.markdown("#### Predicciones de modelos")
                if not model_pred_df.empty:
                    st.dataframe(model_pred_df, use_container_width=True)
                    st.download_button(
                        "Descargar predicciones de modelos (CSV)",
                        dataframe_to_csv_bytes(model_pred_df),
                        "model_predictions.csv",
                        "text/csv",
                    )

    finally:
        db.close()


if __name__ == "__main__":
    main()