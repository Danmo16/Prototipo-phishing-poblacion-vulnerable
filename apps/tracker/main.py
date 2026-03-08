# apps/tracker/main.py
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.domain.models import Event, Target

app = FastAPI(title="Tracker (Academic)")

# GIF 1x1 transparente
PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


def get_target_by_uid(db: Session, uid: str) -> Target | None:
    return db.query(Target).filter(Target.uid == uid).first()


def get_latest_delivered_event(db: Session, target_id: int) -> Event | None:
    return (
        db.query(Event)
        .filter(
            Event.target_id == target_id,
            Event.event_type == "delivered",
        )
        .order_by(Event.occurred_at.desc(), Event.id.desc())
        .first()
    )


@app.get("/open.gif")
def open_pixel(uid: str, db: Session = Depends(get_db)):
    target = get_target_by_uid(db, uid)
    if not target:
        raise HTTPException(status_code=404, detail="UID not found")

    delivered_event = get_latest_delivered_event(db, target.id)
    if not delivered_event:
        raise HTTPException(status_code=404, detail="No delivered event found for this target")

    ev = Event(
        campaign_id=delivered_event.campaign_id,
        target_id=target.id,
        template_id=delivered_event.template_id,
        event_type="opened",
        occurred_at=datetime.utcnow(),
        meta={"uid": uid},
    )
    db.add(ev)
    db.commit()

    return Response(content=PIXEL_GIF, media_type="image/gif")


@app.get("/r")
def redirect_click(uid: str, db: Session = Depends(get_db)):
    target = get_target_by_uid(db, uid)
    if not target:
        raise HTTPException(status_code=404, detail="UID not found")

    delivered_event = get_latest_delivered_event(db, target.id)
    if not delivered_event:
        raise HTTPException(status_code=404, detail="No delivered event found for this target")

    ev = Event(
        campaign_id=delivered_event.campaign_id,
        target_id=target.id,
        template_id=delivered_event.template_id,
        event_type="clicked",
        occurred_at=datetime.utcnow(),
        meta={"uid": uid},
    )
    db.add(ev)
    db.commit()

    return RedirectResponse(url="/landing")


@app.get("/landing")
def landing():
    return {
        "message": "Página educativa: esto fue una simulación académica.",
        "tips": [
            "Verifica el dominio del enlace.",
            "Desconfía de urgencias o recompensas.",
            "Reporta mensajes sospechosos por canales oficiales.",
        ],
    }