# scripts/generate_analytic_pdf_report.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from xhtml2pdf import pisa


REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HTML_PATH = REPORT_DIR / "analytic_report.html"
PDF_PATH = REPORT_DIR / "analytic_report.pdf"


def convert_html_to_pdf(source_html: str, output_path: Path) -> bool:
    with open(output_path, "wb") as output_file:
        result = pisa.CreatePDF(src=source_html, dest=output_file)
    return not result.err


def main():
    if not HTML_PATH.exists():
        raise FileNotFoundError(
            f"No existe {HTML_PATH}. Ejecuta primero: python -m scripts.generate_analytic_html_report"
        )

    html_content = HTML_PATH.read_text(encoding="utf-8")

    ok = convert_html_to_pdf(html_content, PDF_PATH)
    if not ok or not PDF_PATH.exists():
        raise RuntimeError("Falló la conversión de HTML a PDF.")

    print(f"Reporte PDF exportado en: {PDF_PATH.resolve()}")


if __name__ == "__main__":
    main()