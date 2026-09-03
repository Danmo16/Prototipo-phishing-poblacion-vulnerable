from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


def build_timestamp() -> str:
    """
    Genera una marca temporal para identificar una ejecución.
    Ejemplo: 20260902_224530
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_component(value: str) -> str:
    """
    Limpia un texto para que pueda utilizarse de forma segura
    dentro del nombre de un archivo.
    """
    value = str(value).strip().lower()
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value)
    return value.strip("-")


def build_artifact_name(
    artifact: str,
    context: str | None = None,
    timestamp: str | None = None,
    extension: str = "csv",
) -> str:
    """
    Construye nombres versionados para los artefactos.

    Ejemplo:
    analytic_dataset_observed_campaigns-1-9-n9_20260902_224530.csv
    """
    timestamp = timestamp or build_timestamp()

    parts = [sanitize_component(artifact)]

    if context:
        parts.append(sanitize_component(context))

    parts.append(timestamp)

    extension = extension.lstrip(".")

    return "_".join(parts) + f".{extension}"


def latest_artifact(directory: Path, pattern: str) -> Path | None:
    """
    Devuelve el artefacto más reciente que coincida con el patrón.
    """
    matches = [
        path
        for path in directory.glob(pattern)
        if path.is_file()
    ]

    if not matches:
        return None

    return max(matches, key=lambda path: path.stat().st_mtime)


def latest_versioned_or_legacy(
    directory: Path,
    versioned_pattern: str,
    legacy_name: str,
) -> Path | None:
    """
    Busca primero el archivo versionado más reciente.
    Si no existe, permite utilizar el nombre antiguo.
    """
    latest = latest_artifact(directory, versioned_pattern)

    if latest is not None:
        return latest

    legacy = directory / legacy_name

    if legacy.exists():
        return legacy

    return None


def latest_model_run_prefix(
    directory: Path,
    base_prefix: str,
) -> str:
    """
    Obtiene el prefijo completo de la ejecución más reciente
    de un modelo.

    Ejemplo:
    baseline_logreg_combined
    ->
    baseline_logreg_combined_20260902_224530
    """
    latest_metrics = latest_artifact(
        directory,
        f"{base_prefix}_*_metrics.json",
    )

    if latest_metrics is not None:
        suffix = "_metrics.json"
        return latest_metrics.name[:-len(suffix)]

    # Compatibilidad con artefactos antiguos.
    legacy_metrics = directory / f"{base_prefix}_metrics.json"

    if legacy_metrics.exists():
        return base_prefix

    return base_prefix