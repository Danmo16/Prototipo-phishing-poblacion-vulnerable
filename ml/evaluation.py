# ml/evaluation.py
from __future__ import annotations

import math
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


def safe_brier_score(y_true, y_prob) -> float | None:
    try:
        return float(brier_score_loss(y_true, y_prob))
    except Exception:
        return None


def build_calibration_df(y_true, y_prob, n_bins: int = 10) -> pd.DataFrame:
    """
    Construye datos para curva de calibración.
    """
    prob_true, prob_pred = calibration_curve(
        y_true,
        y_prob,
        n_bins=n_bins,
        strategy="quantile",
    )

    return pd.DataFrame(
        {
            "bin": list(range(1, len(prob_true) + 1)),
            "predicted_probability_mean": prob_pred,
            "observed_positive_rate": prob_true,
        }
    )


def build_lift_table(y_true, y_prob, n_bins: int = 10) -> pd.DataFrame:
    """
    Construye tabla de gains/lift ordenando por score descendente.
    """
    df = pd.DataFrame(
        {
            "y_true": list(y_true),
            "y_prob": list(y_prob),
        }
    ).sort_values("y_prob", ascending=False).reset_index(drop=True)

    if df.empty:
        return pd.DataFrame()

    total_positives = df["y_true"].sum()
    total_rows = len(df)
    overall_rate = total_positives / total_rows if total_rows > 0 else 0.0

    # Crear deciles/cuantiles
    df["bucket"] = pd.qcut(
        df.index + 1,
        q=min(n_bins, len(df)),
        labels=False,
        duplicates="drop",
    ) + 1

    grouped = (
        df.groupby("bucket", dropna=False)
        .agg(
            rows=("y_true", "count"),
            positives=("y_true", "sum"),
            min_score=("y_prob", "min"),
            max_score=("y_prob", "max"),
            avg_score=("y_prob", "mean"),
        )
        .reset_index()
        .sort_values("bucket")
    )

    grouped["positive_rate"] = grouped["positives"] / grouped["rows"]
    grouped["lift"] = grouped["positive_rate"].apply(
        lambda x: (x / overall_rate) if overall_rate > 0 else math.nan
    )

    grouped["cumulative_rows"] = grouped["rows"].cumsum()
    grouped["cumulative_positives"] = grouped["positives"].cumsum()
    grouped["cumulative_positive_capture_rate"] = grouped["cumulative_positives"].apply(
        lambda x: (x / total_positives) if total_positives > 0 else 0.0
    )

    return grouped