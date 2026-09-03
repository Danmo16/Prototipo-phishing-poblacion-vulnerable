from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.artifact_utils import (
    build_timestamp,
    build_artifact_name,
    latest_artifact,
)


EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    observed_path = latest_artifact(
        EXPORT_DIR,
        "analytic_dataset_observed_*.csv",
    )

    synthetic_path = latest_artifact(
        EXPORT_DIR,
        "analytic_dataset_synthetic_*.csv",
    )

    if observed_path is None:
        raise FileNotFoundError(
            "No se encontró ningún dataset observado versionado. "
            "Ejecuta primero: python -m scripts.export_dataset"
        )

    if synthetic_path is None:
        raise FileNotFoundError(
            "No se encontró ningún dataset sintético versionado. "
            "Ejecuta primero: python -m scripts.generate_synthetic_dataset"
        )

    observed = pd.read_csv(observed_path)
    synthetic = pd.read_csv(synthetic_path)

    if "source" not in observed.columns:
        observed["source"] = "observed"

    if "source" not in synthetic.columns:
        synthetic["source"] = "synthetic"

    combined = pd.concat(
        [observed, synthetic],
        ignore_index=True,
    )

    timestamp = build_timestamp()

    merged_path = EXPORT_DIR / build_artifact_name(
        artifact="analytic_dataset_combined",
        timestamp=timestamp,
        extension="csv",
    )

    combined.to_csv(
        merged_path,
        index=False,
        encoding="utf-8",
    )

    print("Dataset combinado generado correctamente.")
    print(f"Dataset observado utilizado: {observed_path.resolve()}")
    print(f"Dataset sintético utilizado: {synthetic_path.resolve()}")
    print(f"Dataset combinado exportado: {merged_path.resolve()}")
    print(f"Filas observadas: {len(observed)}")
    print(f"Filas sintéticas: {len(synthetic)}")
    print(f"Filas totales: {len(combined)}")


if __name__ == "__main__":
    main()