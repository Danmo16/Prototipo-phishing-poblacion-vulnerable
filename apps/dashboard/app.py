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

    open_rate = round((total_opened / total_delivered) * 100, 2) if total_delivered else 0.0
    click_rate = round((total_clicked / total_delivered) * 100, 2) if total_delivered else 0.0

    return {
        "campaigns": total_campaigns,
        "targets": total_targets,
        "templates": total_templates,
        "segments": total_segments,
        "events": total_events,
        "delivered": total_delivered,
        "opened": total_opened,
        "clicked": total_clicked,
        "open_rate": open_rate,
        "click_rate": click_rate,
    }


def load_campaigns_df(db: Session) -> pd.DataFrame:
    rows = db.query(Campaign).order_by(Campaign.id.desc()).all()

    data = [
        {
            "id": c.id,
            "channel": c.channel,
            "status": c.status,
            "launched_at": c.launched_at,
            "template_id": c.template_id,
            "segment_id": c.segment_id,
        }
        for c in rows
    ]
    return pd.DataFrame(data)


def load_targets_df(db: Session) -> pd.DataFrame:
    rows = db.query(Target).order_by(Target.id.desc()).all()

    data = [
        {
            "id": t.id,
            "segment_id": t.segment_id,
            "recipient": t.recipient,
            "uid": t.uid,
            "meta": t.meta,
        }
        for t in rows
    ]
    return pd.DataFrame(data)


def load_templates_df(db: Session) -> pd.DataFrame:
    rows = db.query(Template).order_by(Template.id.desc()).all()

    data = [
        {
            "id": t.id,
            "channel": t.channel,
            "name": t.name,
            "signals": t.signals,
            "version": t.version,
        }
        for t in rows
    ]
    return pd.DataFrame(data)


def load_segments_df(db: Session) -> pd.DataFrame:
    rows = db.query(Segment).order_by(Segment.id.desc()).all()

    data = [
        {
            "id": s.id,
            "age_bracket": s.age_bracket,
            "gender": s.gender,
            "education": s.education,
        }
        for s in rows
    ]
    return pd.DataFrame(data)


def load_events_df(
    db: Session,
    campaign_id: int | None = None,
    event_type: str | None = None,
) -> pd.DataFrame:
    query = db.query(Event).order_by(Event.id.desc())

    if campaign_id is not None:
        query = query.filter(Event.campaign_id == campaign_id)

    if event_type and event_type != "Todos":
        query = query.filter(Event.event_type == event_type)

    rows = query.all()

    data = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "occurred_at": e.occurred_at,
            "campaign_id": e.campaign_id,
            "target_id": e.target_id,
            "template_id": e.template_id,
            "meta": e.meta,
        }
        for e in rows
    ]
    return pd.DataFrame(data)


def load_event_summary_df(db: Session) -> pd.DataFrame:
    rows = (
        db.query(Event.event_type, func.count(Event.id))
        .group_by(Event.event_type)
        .all()
    )

    data = [{"event_type": r[0], "count": r[1]} for r in rows]
    return pd.DataFrame(data)


def load_campaign_summary_df(db: Session) -> pd.DataFrame:
    campaigns = db.query(Campaign).order_by(Campaign.id.asc()).all()
    summary = []

    for camp in campaigns:
        delivered = (
            db.query(func.count(Event.id))
            .filter(Event.campaign_id == camp.id, Event.event_type == "delivered")
            .scalar()
            or 0
        )
        opened = (
            db.query(func.count(Event.id))
            .filter(Event.campaign_id == camp.id, Event.event_type == "opened")
            .scalar()
            or 0
        )
        clicked = (
            db.query(func.count(Event.id))
            .filter(Event.campaign_id == camp.id, Event.event_type == "clicked")
            .scalar()
            or 0
        )

        open_rate = round((opened / delivered) * 100, 2) if delivered else 0.0
        click_rate = round((clicked / delivered) * 100, 2) if delivered else 0.0

        summary.append(
            {
                "campaign_id": camp.id,
                "channel": camp.channel,
                "status": camp.status,
                "segment_id": camp.segment_id,
                "template_id": camp.template_id,
                "delivered": delivered,
                "opened": opened,
                "clicked": clicked,
                "open_rate_pct": open_rate,
                "click_rate_pct": click_rate,
            }
        )

    return pd.DataFrame(summary)


def load_segment_summary_df(db: Session) -> pd.DataFrame:
    segments = db.query(Segment).order_by(Segment.id.asc()).all()
    summary = []

    for seg in segments:
        target_ids = [t.id for t in seg.targets]

        if not target_ids:
            summary.append(
                {
                    "segment_id": seg.id,
                    "age_bracket": seg.age_bracket,
                    "gender": seg.gender,
                    "education": seg.education,
                    "targets": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "open_rate_pct": 0.0,
                    "click_rate_pct": 0.0,
                }
            )
            continue

        delivered = (
            db.query(func.count(Event.id))
            .filter(Event.target_id.in_(target_ids), Event.event_type == "delivered")
            .scalar()
            or 0
        )
        opened = (
            db.query(func.count(Event.id))
            .filter(Event.target_id.in_(target_ids), Event.event_type == "opened")
            .scalar()
            or 0
        )
        clicked = (
            db.query(func.count(Event.id))
            .filter(Event.target_id.in_(target_ids), Event.event_type == "clicked")
            .scalar()
            or 0
        )

        open_rate = round((opened / delivered) * 100, 2) if delivered else 0.0
        click_rate = round((clicked / delivered) * 100, 2) if delivered else 0.0

        summary.append(
            {
                "segment_id": seg.id,
                "age_bracket": seg.age_bracket,
                "gender": seg.gender,
                "education": seg.education,
                "targets": len(target_ids),
                "delivered": delivered,
                "opened": opened,
                "clicked": clicked,
                "open_rate_pct": open_rate,
                "click_rate_pct": click_rate,
            }
        )

    return pd.DataFrame(summary)


def load_template_signal_summary_df(db: Session) -> pd.DataFrame:
    templates = db.query(Template).order_by(Template.id.asc()).all()
    rows = []

    for tpl in templates:
        delivered = (
            db.query(func.count(Event.id))
            .filter(Event.template_id == tpl.id, Event.event_type == "delivered")
            .scalar()
            or 0
        )
        opened = (
            db.query(func.count(Event.id))
            .filter(Event.template_id == tpl.id, Event.event_type == "opened")
            .scalar()
            or 0
        )
        clicked = (
            db.query(func.count(Event.id))
            .filter(Event.template_id == tpl.id, Event.event_type == "clicked")
            .scalar()
            or 0
        )

        open_rate = round((opened / delivered) * 100, 2) if delivered else 0.0
        click_rate = round((clicked / delivered) * 100, 2) if delivered else 0.0

        rows.append(
            {
                "template_id": tpl.id,
                "template_name": tpl.name,
                "signals": tpl.signals,
                "delivered": delivered,
                "opened": opened,
                "clicked": clicked,
                "open_rate_pct": open_rate,
                "click_rate_pct": click_rate,
            }
        )

    return pd.DataFrame(rows)


def build_academic_summary(metrics: dict) -> pd.DataFrame:
    rows = [
        {"indicador": "Total de campañas", "valor": metrics["campaigns"]},
        {"indicador": "Total de targets", "valor": metrics["targets"]},
        {"indicador": "Total de eventos", "valor": metrics["events"]},
        {"indicador": "Correos entregados", "valor": metrics["delivered"]},
        {"indicador": "Aperturas registradas", "valor": metrics["opened"]},
        {"indicador": "Clics registrados", "valor": metrics["clicked"]},
        {"indicador": "Tasa global de apertura (%)", "valor": metrics["open_rate"]},
        {"indicador": "Tasa global de clic (%)", "valor": metrics["click_rate"]},
    ]
    return pd.DataFrame(rows)


def main():
    st.title("📊 Dashboard - Prototipo de Phishing")
    st.write(
        "Panel de visualización para campañas, destinatarios, eventos y métricas "
        "del prototipo académico."
    )

    db = get_db()

    try:
        metrics = load_metrics(db)
        campaigns_df = load_campaigns_df(db)
        targets_df = load_targets_df(db)
        templates_df = load_templates_df(db)
        segments_df = load_segments_df(db)
        campaign_summary_df = load_campaign_summary_df(db)
        segment_summary_df = load_segment_summary_df(db)
        template_signal_df = load_template_signal_summary_df(db)
        event_summary_df = load_event_summary_df(db)
        academic_summary_df = build_academic_summary(metrics)

        # KPIs
        st.subheader("Resumen general")
        c1, c2, c3, c4, c5 = st.columns(5)
        c6, c7, c8, c9 = st.columns(4)

        c1.metric("Campañas", metrics["campaigns"])
        c2.metric("Targets", metrics["targets"])
        c3.metric("Templates", metrics["templates"])
        c4.metric("Segments", metrics["segments"])
        c5.metric("Eventos", metrics["events"])

        c6.metric("Delivered", metrics["delivered"])
        c7.metric("Opened", metrics["opened"])
        c8.metric("Clicked", metrics["clicked"])
        c9.metric("Open / Click Rate", f'{metrics["open_rate"]}% / {metrics["click_rate"]}%')

        st.divider()

        # Exportación CSV
        st.subheader("Exportación de datos")
        d1, d2, d3 = st.columns(3)

        with d1:
            st.download_button(
                label="Descargar campañas (CSV)",
                data=dataframe_to_csv_bytes(campaigns_df),
                file_name="campaigns.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Descargar targets (CSV)",
                data=dataframe_to_csv_bytes(targets_df),
                file_name="targets.csv",
                mime="text/csv",
            )

        with d2:
            st.download_button(
                label="Descargar eventos (CSV)",
                data=dataframe_to_csv_bytes(load_events_df(db)),
                file_name="events.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Descargar resumen por campaña (CSV)",
                data=dataframe_to_csv_bytes(campaign_summary_df),
                file_name="campaign_summary.csv",
                mime="text/csv",
            )

        with d3:
            st.download_button(
                label="Descargar resumen por segmento (CSV)",
                data=dataframe_to_csv_bytes(segment_summary_df),
                file_name="segment_summary.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Descargar resumen académico (CSV)",
                data=dataframe_to_csv_bytes(academic_summary_df),
                file_name="academic_summary.csv",
                mime="text/csv",
            )

        st.divider()

        # Resumen académico para tesis
        st.subheader("Indicadores académicos para tesis")
        st.dataframe(academic_summary_df, use_container_width=True)

        st.markdown("### Interpretación general")
        st.write(
            "Estos indicadores permiten sustentar el comportamiento global del prototipo, "
            "mostrar el volumen de observaciones recolectadas y evidenciar la respuesta "
            "de los usuarios frente a las campañas simuladas."
        )

        st.divider()

        # Campañas
        st.subheader("Campañas")
        if campaigns_df.empty:
            st.info("No hay campañas registradas.")
        else:
            st.dataframe(campaigns_df, use_container_width=True)

        st.divider()

        # Resumen por campaña
        st.subheader("Resumen por campaña")
        if campaign_summary_df.empty:
            st.info("No hay datos de campañas para resumir.")
        else:
            st.dataframe(campaign_summary_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.caption("Tasa de apertura por campaña (%)")
                st.bar_chart(
                    campaign_summary_df.set_index("campaign_id")[["open_rate_pct"]]
                )
            with col2:
                st.caption("Tasa de clic por campaña (%)")
                st.bar_chart(
                    campaign_summary_df.set_index("campaign_id")[["click_rate_pct"]]
                )

        st.divider()

        # Resumen por segmento
        st.subheader("Resumen por segmento")
        if segment_summary_df.empty:
            st.info("No hay datos de segmentos para resumir.")
        else:
            st.dataframe(segment_summary_df, use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                st.caption("Tasa de apertura por segmento (%)")
                st.bar_chart(
                    segment_summary_df.set_index("segment_id")[["open_rate_pct"]]
                )
            with col4:
                st.caption("Tasa de clic por segmento (%)")
                st.bar_chart(
                    segment_summary_df.set_index("segment_id")[["click_rate_pct"]]
                )

        st.divider()

        # Resumen por plantilla / señales
        st.subheader("Resumen por plantilla y señales")
        if template_signal_df.empty:
            st.info("No hay datos de plantillas para resumir.")
        else:
            st.dataframe(template_signal_df, use_container_width=True)

            col5, col6 = st.columns(2)
            with col5:
                st.caption("Tasa de apertura por plantilla (%)")
                st.bar_chart(
                    template_signal_df.set_index("template_id")[["open_rate_pct"]]
                )
            with col6:
                st.caption("Tasa de clic por plantilla (%)")
                st.bar_chart(
                    template_signal_df.set_index("template_id")[["click_rate_pct"]]
                )

        st.divider()

        # Targets
        st.subheader("Targets")
        if targets_df.empty:
            st.info("No hay targets registrados.")
        else:
            st.dataframe(targets_df, use_container_width=True)

        st.divider()

        # Eventos con filtros
        st.subheader("Eventos")

        campaign_options = ["Todas"]
        if not campaigns_df.empty:
            campaign_options += campaigns_df["id"].tolist()

        event_type_options = ["Todos", "delivered", "opened", "clicked", "reported"]

        f1, f2 = st.columns(2)
        selected_campaign = f1.selectbox("Filtrar por campaña", campaign_options)
        selected_event_type = f2.selectbox("Filtrar por tipo de evento", event_type_options)

        campaign_filter = None if selected_campaign == "Todas" else int(selected_campaign)

        events_df = load_events_df(
            db,
            campaign_id=campaign_filter,
            event_type=selected_event_type,
        )

        if events_df.empty:
            st.info("No hay eventos para los filtros seleccionados.")
        else:
            st.dataframe(events_df, use_container_width=True)

        st.divider()

        # Conteo por tipo de evento
        st.subheader("Conteo por tipo de evento")
        if event_summary_df.empty:
            st.info("No hay datos de eventos para resumir.")
        else:
            st.dataframe(event_summary_df, use_container_width=True)
            st.bar_chart(event_summary_df.set_index("event_type"))

        st.divider()

        # Exportaciones adicionales
        st.subheader("Exportaciones académicas adicionales")
        e1, e2 = st.columns(2)

        with e1:
            st.download_button(
                label="Descargar resumen por plantilla/señales (CSV)",
                data=dataframe_to_csv_bytes(template_signal_df),
                file_name="template_signal_summary.csv",
                mime="text/csv",
            )

        with e2:
            st.download_button(
                label="Descargar conteo por tipo de evento (CSV)",
                data=dataframe_to_csv_bytes(event_summary_df),
                file_name="event_type_summary.csv",
                mime="text/csv",
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()