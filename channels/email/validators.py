# channels/email/validators.py
from __future__ import annotations

from typing import Any


REQUIRED_PLACEHOLDERS = [
    "{{ landing_url }}",
    "{{ tracking_dot }}",
]

RECOMMENDED_PLACEHOLDERS = [
    "{{ report_url }}",
]


def validate_email_template(html_body: str, subject: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not html_body or not html_body.strip():
        errors.append("html_body is required")

    if subject is None or not str(subject).strip():
        errors.append("subject is required")

    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder not in html_body:
            errors.append(f"missing placeholder: {placeholder}")

    for placeholder in RECOMMENDED_PLACEHOLDERS:
        if placeholder not in html_body:
            warnings.append(f"recommended placeholder not found: {placeholder}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }