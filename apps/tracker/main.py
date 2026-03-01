# apps/tracker/main.py
from fastapi import FastAPI, Depends
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime

from core.db.session import get_db
from core.domain.models import Event

app = FastAPI(title="Tracker (Academic)")

# GIF 1x1 transparente (bytes mínimos)
PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)

@app.get("/open.gif")
def open_pixel(uid: str, campaign_id: int, target_id: int, template_id: int, db: Session = Depends(get_db)):
    # Registro de apertura (simulación)
    ev = Event(
        campaign_id=campaign_id,
        target_id=target_id,
        template_id=template_id,
        event_type="opened",
        occurred_at=datetime.utcnow(),
        meta={"uid": uid},
    )
    db.add(ev)
    db.commit()
    return Response(content=PIXEL_GIF, media_type="image/gif")

@app.get("/r")
def redirect_click(uid: str, campaign_id: int, target_id: int, template_id: int, db: Session = Depends(get_db)):
    # Registro de clic (simulación)
    ev = Event(
        campaign_id=campaign_id,
        target_id=target_id,
        template_id=template_id,
        event_type="clicked",
        occurred_at=datetime.utcnow(),
        meta={"uid": uid},
    )
    db.add(ev)
    db.commit()
    # landing educativa fija (ajústala luego)
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