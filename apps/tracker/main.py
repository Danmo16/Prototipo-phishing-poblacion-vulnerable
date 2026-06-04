# apps/tracker/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from core.db.session import SessionLocal
from core.domain.models import Event, Target

app = FastAPI(
    title="Tracker Service",
    version="0.1.0",
)


PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


def get_db() -> Session:
    return SessionLocal()


def get_target_and_context_by_uid(db: Session, uid: str) -> tuple[Target, Event | None]:
    target = db.query(Target).filter(Target.uid == uid).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    last_delivered = (
        db.query(Event)
        .filter(
            Event.target_id == target.id,
            Event.event_type == "delivered",
        )
        .order_by(Event.id.desc())
        .first()
    )

    return target, last_delivered


@app.get("/landing", response_class=HTMLResponse)
def landing():
    return """
    <html>
      <head><title>Landing educativa</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto;">
        <h1>Simulación académica de phishing</h1>
        <p>Esta página forma parte de una simulación controlada con fines educativos y de investigación.</p>
        <p>El objetivo es analizar patrones de interacción ante correos simulados y fortalecer la concienciación.</p>
      </body>
    </html>
    """


@app.get("/reported", response_class=HTMLResponse)
def reported_page():
    return """
    <html>
      <head><title>Reporte registrado</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto;">
        <h1>Reporte registrado</h1>
        <p>Gracias. El mensaje ha sido marcado como reportado dentro de la simulación académica.</p>
        <p>Este comportamiento es valioso para el análisis de concienciación y respuesta del usuario.</p>
      </body>
    </html>
    """


@app.get("/open.gif")
def track_open(uid: str):
    db = get_db()
    try:
        target, last_delivered = get_target_and_context_by_uid(db, uid)

        if last_delivered:
            event = Event(
                campaign_id=last_delivered.campaign_id,
                target_id=target.id,
                template_id=last_delivered.template_id,
                event_type="opened",
                meta={"uid": uid},
            )
            db.add(event)
            db.commit()

        return Response(content=PIXEL_GIF, media_type="image/gif")
    finally:
        db.close()


@app.get("/r")
def track_click(uid: str):
    db = get_db()
    try:
        target, last_delivered = get_target_and_context_by_uid(db, uid)

        if last_delivered:
            event = Event(
                campaign_id=last_delivered.campaign_id,
                target_id=target.id,
                template_id=last_delivered.template_id,
                event_type="clicked",
                meta={"uid": uid},
            )
            db.add(event)
            db.commit()

        return RedirectResponse(url="/landing")
    finally:
        db.close()


@app.get("/report")
def report_phishing(uid: str):
    db = get_db()
    try:
        target, last_delivered = get_target_and_context_by_uid(db, uid)

        if last_delivered:
            event = Event(
                campaign_id=last_delivered.campaign_id,
                target_id=target.id,
                template_id=last_delivered.template_id,
                event_type="reported",
                meta={"uid": uid},
            )
            db.add(event)
            db.commit()

        return RedirectResponse(url="/reported")
    finally:
        db.close()