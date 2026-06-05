# scripts/generate_ethics_protocol_report.py
from __future__ import annotations

from pathlib import Path


DOCS_DIR = Path("docs/ethics")
REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PROTOCOL_PATH = DOCS_DIR / "protocol_no_human_testing.md"
CHECKLIST_PATH = DOCS_DIR / "execution_checklist_no_humans.md"
RISK_PATH = DOCS_DIR / "risk_matrix_no_humans.md"

OUTPUT_HTML = REPORT_DIR / "ethics_protocol_report.html"


def read_text(path: Path) -> str:
    if not path.exists():
        return f"No existe el archivo: {path}"
    return path.read_text(encoding="utf-8")


def md_like_to_html(text: str) -> str:
    lines = text.splitlines()
    html_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("- [ ] "):
            html_lines.append(f"<p>☐ {stripped[6:]}</p>")
        elif stripped.startswith("- "):
            html_lines.append(f"<p>• {stripped[2:]}</p>")
        elif stripped.startswith("|"):
            # tabla simple preformateada
            html_lines.append(f"<pre>{line}</pre>")
        elif stripped == "":
            html_lines.append("<br/>")
        else:
            html_lines.append(f"<p>{stripped}</p>")

    return "\n".join(html_lines)


def main():
    protocol_text = read_text(PROTOCOL_PATH)
    checklist_text = read_text(CHECKLIST_PATH)
    risk_text = read_text(RISK_PATH)

    html = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Protocolo Ético del Prototipo</title>
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                margin: 40px;
                color: #1f2937;
            }}
            h1 {{
                border-bottom: 3px solid #2563eb;
                padding-bottom: 10px;
            }}
            h2 {{
                margin-top: 32px;
                color: #111827;
            }}
            h3 {{
                margin-top: 20px;
                color: #374151;
            }}
            p {{
                line-height: 1.5;
            }}
            .section {{
                margin-top: 28px;
            }}
            .note {{
                background: #eff6ff;
                border-left: 4px solid #2563eb;
                padding: 12px;
                margin-bottom: 20px;
            }}
            pre {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                padding: 8px;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <h1>Protocolo ético y metodológico del prototipo</h1>

        <div class="note">
            Este documento formaliza la restricción de no ejecutar pruebas reales con sujetos humanos,
            manteniendo el proyecto dentro de un alcance técnico, académico y controlado.
        </div>

        <div class="section">
            {md_like_to_html(protocol_text)}
        </div>

        <div class="section">
            <h2>Checklist operativa</h2>
            {md_like_to_html(checklist_text)}
        </div>

        <div class="section">
            <h2>Matriz de riesgos y controles</h2>
            {md_like_to_html(risk_text)}
        </div>
    </body>
    </html>
    """

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Reporte ético exportado en: {OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()