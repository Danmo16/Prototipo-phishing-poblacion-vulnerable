# scripts/validate_sqlite_compatibility.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config.settings import settings
from core.db.session import SessionLocal
from core.domain.models import Segment, Template, Target, Campaign


SQLITE_DIR = Path("data/sqlite")
SQLITE_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Validación de compatibilidad con SQLite")
    print("=" * 60)
    print(f"DATABASE_URL actual: {settings.database_url}")

    if not settings.database_url.startswith("sqlite"):
        raise ValueError(
            "La validación SQLite requiere una DATABASE_URL con prefijo sqlite. "
            "Cambia el .env temporalmente antes de ejecutar este script."
        )

    db: Session = SessionLocal()

    try:
        print("1. Probando conexión...")
        db.execute(text("SELECT 1"))
        print("   OK conexión SQLite")

        print("2. Insertando datos mínimos de prueba...")

        segment = Segment(
            age_bracket="25-34",
            gender="M",
            education="Universitaria",
        )
        db.add(segment)
        db.flush()

        template = Template(
            channel="email",
            name="SQLite test template",
            subject="Prueba SQLite para {{ name }}",
            description="Template de prueba SQLite",
            html_body=(
                "<html><body>"
                "<p>Hola {{ name }}</p>"
                "<p><a href='{{ landing_url }}'>Abrir</a></p>"
                "<p><a href='{{ report_url }}'>Reportar</a></p>"
                "<img src='{{ tracking_dot }}' width='1' height='1' />"
                "</body></html>"
            ),
            signals={
                "urgencia": 0,
                "autoridad": 1,
                "recompensa": 0,
                "personalizacion": 1,
            },
            version=1,
        )
        db.add(template)
        db.flush()

        target = Target(
            segment_id=segment.id,
            recipient="sqlite_test@example.com",
            meta={"source": "sqlite_validation"},
        )
        db.add(target)
        db.flush()

        campaign = Campaign(
            channel="email",
            template_id=template.id,
            segment_id=segment.id,
            status="draft",
        )
        db.add(campaign)
        db.commit()

        print("   OK inserciones mínimas")

        print("3. Verificando lectura...")
        segment_count = db.query(Segment).count()
        template_count = db.query(Template).count()
        target_count = db.query(Target).count()
        campaign_count = db.query(Campaign).count()

        print(f"   Segments: {segment_count}")
        print(f"   Templates: {template_count}")
        print(f"   Targets: {target_count}")
        print(f"   Campaigns: {campaign_count}")

        print("4. Validación final...")
        if min(segment_count, template_count, target_count, campaign_count) < 1:
            raise RuntimeError("La validación SQLite no pasó correctamente.")

        print("✅ Compatibilidad básica con SQLite validada correctamente.")

    finally:
        db.close()


if __name__ == "__main__":
    main()