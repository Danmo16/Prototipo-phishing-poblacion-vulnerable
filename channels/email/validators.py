# channels/email/validators.py
from __future__ import annotations

from typing import Any


REQUIRED_PLACEHOLDERS = [
    "{{ landing_url }}",
    "{{ tracking_dot }}",
]


def validate_email_template(html_body: str, subject: str | None = None) -> dict[str, Any]:
    """
    Validates the minimum structure expected for an email template.

    Rules for the academic MVP:
    - html_body must not be empty
    - subject should not be empty
    - html_body must include required placeholders for tracker integration
    """
    errors: list[str] = []

    if not html_body or not html_body.strip():
        errors.append("html_body is required")

    if subject is None or not str(subject).strip():
        errors.append("subject is required")

    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder not in html_body:
            errors.append(f"missing placeholder: {placeholder}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }