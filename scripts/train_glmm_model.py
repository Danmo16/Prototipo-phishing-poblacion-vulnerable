# scripts/train_glmm_model.py
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ml.preprocessing import clean_dataset


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATASET_PATH = EXPORT_DIR / "analytic_dataset_combined.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entrena un GLMM binomial exploratorio para clicked_flag."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(DEFAULT_DATASET_PATH),
        help="Ruta al dataset CSV a utilizar.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="glmm_clicked",
        help="Prefijo de archivos de salida en data/models.",
    )
    parser.add_argument(
        "--random-effect",
        type=str,
        default="segment_id",
        choices=["segment_id", "campaign_id"],
        help="Grupo para intercepto aleatorio.",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="vb",
        choices=["vb", "map"],
        help="Método de ajuste: vb=variational Bayes, map=Laplace/MAP.",
    )
    return parser.parse_args()


def prepare_dataset(df: pd.DataFrame, random_effect: str) -> pd.DataFrame:
    df = clean_dataset(df).copy()

    required_cols = [
        "clicked_flag",
        "signal_urgency",
        "signal_authority",
        "signal_reward",
        "signal_personalization",
        "age_bracket",
        "gender",
        "education",
        random_effect,
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas para GLMM: {missing}")

    df = df.dropna(subset=["clicked_flag", random_effect]).copy()

    # Asegurar tipos
    df["clicked_flag"] = df["clicked_flag"].astype(int)
    df[random_effect] = df[random_effect].astype(str)
    df["age_bracket"] = df["age_bracket"].fillna("Unknown").astype(str)
    df["gender"] = df["gender"].fillna("Unknown").astype(str)
    df["education"] = df["education"].fillna("Unknown").astype(str)

    for col in [
        "signal_urgency",
        "signal_authority",
        "signal_reward",
        "signal_personalization",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


def build_formulas(random_effect: str) -> tuple[str, dict]:
    fixed_formula = (
        "clicked_flag ~ signal_urgency + signal_authority + "
        "signal_reward + signal_personalization + "
        "C(age_bracket) + C(gender) + C(education)"
    )

    vc_formulas = {
        f"re_{random_effect}": f"0 + C({random_effect})"
    }
    return fixed_formula, vc_formulas


def extract_fixed_effects(result) -> pd.DataFrame:
    names = list(result.model.exog_names)
    values = np.asarray(result.fe_mean)
    if hasattr(result, "fe_sd"):
        sd = np.asarray(result.fe_sd)
    else:
        sd = np.full_like(values, np.nan, dtype=float)

    df = pd.DataFrame(
        {
            "term": names,
            "posterior_mean": values,
            "posterior_sd": sd,
            "odds_ratio_approx": np.exp(values),
        }
    ).sort_values("term")
    return df


def extract_variance_components(result) -> pd.DataFrame:
    names = list(result.model.vcp_names)
    values = np.asarray(result.vcp_mean)
    if hasattr(result, "vcp_sd"):
        sd = np.asarray(result.vcp_sd)
    else:
        sd = np.full_like(values, np.nan, dtype=float)

    return pd.DataFrame(
        {
            "component": names,
            "posterior_mean_log_sd": values,
            "posterior_sd_log_sd": sd,
            "sd_approx": np.exp(values),
        }
    )


def main():
    args = parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"No existe {dataset_path}")

    raw_df = pd.read_csv(dataset_path)
    df = prepare_dataset(raw_df, random_effect=args.random_effect)

    if len(df) < 20 or df["clicked_flag"].nunique() < 2:
        raise ValueError(
            "No hay suficientes datos o clases para GLMM. "
            "Se requieren al menos 20 filas y dos clases en clicked_flag."
        )

    fixed_formula, vc_formulas = build_formulas(args.random_effect)

    model = sm.BinomialBayesMixedGLM.from_formula(
        fixed_formula,
        vc_formulas,
        df,
        vcp_p=1.0,
        fe_p=2.0,
    )

    if args.method == "map":
        result = model.fit_map()
    else:
        result = model.fit_vb()

    fixed_df = extract_fixed_effects(result)
    vc_df = extract_variance_components(result)

    pred_prob = result.predict()
    pred_df = df.copy()
    pred_df["glmm_pred_clicked_prob"] = pred_prob
    pred_df["glmm_pred_clicked_flag"] = (pred_df["glmm_pred_clicked_prob"] >= 0.5).astype(int)

    metrics = {
        "model": "glmm_binomial",
        "dataset_path": str(dataset_path.resolve()),
        "output_prefix": args.output_prefix,
        "random_effect": args.random_effect,
        "method": args.method,
        "n_rows": int(len(df)),
        "positive_cases_total": int(df["clicked_flag"].sum()),
        "formula_fixed": fixed_formula,
        "vc_formulas": vc_formulas,
    }

    metrics_path = MODEL_DIR / f"{args.output_prefix}_metrics.json"
    fixed_path = MODEL_DIR / f"{args.output_prefix}_fixed_effects.csv"
    vc_path = MODEL_DIR / f"{args.output_prefix}_variance_components.csv"
    pred_path = MODEL_DIR / f"{args.output_prefix}_predictions.csv"
    summary_path = MODEL_DIR / f"{args.output_prefix}_summary.txt"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    fixed_df.to_csv(fixed_path, index=False, encoding="utf-8")
    vc_df.to_csv(vc_path, index=False, encoding="utf-8")
    pred_df.to_csv(pred_path, index=False, encoding="utf-8")

    summary_text = str(result.summary())
    summary_path.write_text(summary_text, encoding="utf-8")

    print("GLMM exportado correctamente.")
    print(f"Métricas: {metrics_path.resolve()}")
    print(f"Efectos fijos: {fixed_path.resolve()}")
    print(f"Varianza aleatoria: {vc_path.resolve()}")
    print(f"Predicciones: {pred_path.resolve()}")
    print(f"Resumen: {summary_path.resolve()}")


if __name__ == "__main__":
    main()