# scripts/merge_observed_and_synthetic.py
from pathlib import Path
import pandas as pd

EXPORT_DIR = Path("data/exports")

observed_path = EXPORT_DIR / "analytic_dataset.csv"
synthetic_path = EXPORT_DIR / "analytic_dataset_synthetic.csv"
merged_path = EXPORT_DIR / "analytic_dataset_combined.csv"

observed = pd.read_csv(observed_path)
synthetic = pd.read_csv(synthetic_path)

if "source" not in observed.columns:
    observed["source"] = "observed"

if "source" not in synthetic.columns:
    synthetic["source"] = "synthetic"

combined = pd.concat([observed, synthetic], ignore_index=True)
combined.to_csv(merged_path, index=False, encoding="utf-8")

print(f"Dataset combinado exportado en: {merged_path.resolve()}")
print(f"Filas observadas: {len(observed)}")
print(f"Filas sintéticas: {len(synthetic)}")
print(f"Filas totales: {len(combined)}")