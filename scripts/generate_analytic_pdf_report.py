# scripts/generate_analytic_pdf_report.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from xhtml2pdf import pisa

from scripts.artifact_utils import (
    latest_versioned_or_legacy,
)


REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def convert_html_to_pdf(source_html: str, output_path: Path) -> bool:
    with open(output_path, "wb") as output_file:
        result = pisa.CreatePDF(src=source_html, dest=output_file)
    return not result.err


def main():
    html_path = latest_versioned_or_legacy(
        REPORT_DIR,
        "analytic_report_*.html",
        "analytic_report.html",
    )

    if html_path is None:
        raise FileNotFoundError(
            "No se encontró ningún reporte HTML. "
            "Ejecuta primero: "
            "python -m scripts.generate_analytic_html_report"
        )

    pdf_path = html_path.with_suffix(".pdf")

    html_content = html_path.read_text(
        encoding="utf-8"
    )

    ok = convert_html_to_pdf(
        html_content,
        pdf_path,
    )

    if not ok or not pdf_path.exists():
        raise RuntimeError(
            "Falló la conversión de HTML a PDF."
        )

    print(f"HTML utilizado: {html_path.resolve()}")
    print(f"Reporte PDF exportado en: {pdf_path.resolve()}")


if __name__ == "__main__":
    main()