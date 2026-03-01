# scripts/seed.py
from core.db.session import db_session
from core.domain.models import Segment, Template, Campaign

SAFE_EMAIL_TEMPLATE = """
<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif;">
    <h3>Simulación académica de concienciación</h3>
    <p>Hola {{name}},</p>
    <p>Este mensaje es parte de un ejercicio controlado de aprendizaje.</p>
    <p>
      <a href="{{landing_url}}">Abrir página educativa</a>
    </p>
    <img src="{{tracking_dot}}" width="1" height="1" alt="" />
  </body>
</html>
"""

def main():
    with db_session() as db:
        seg = Segment(age_bracket="18-24", gender="N/A", education="Universitaria")
        db.add(seg)
        db.flush()

        tpl = Template(
            channel="email",
            name="Template educativo v1",
            html_body=SAFE_EMAIL_TEMPLATE,
            signals={"urgencia": 0, "autoridad": 0, "recompensa": 0, "personalizacion": 0},
            version=1,
        )
        db.add(tpl)
        db.flush()

        camp = Campaign(channel="email", status="draft", template_id=tpl.id, segment_id=seg.id)
        db.add(camp)

    print("Seed OK: created Segment, Template, Campaign (draft).")

if __name__ == "__main__":
    main()