# scripts/train_baseline_model.py
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import json
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

from ml.preprocessing import clean_dataset, get_feature_matrix
from ml.evaluation import safe_brier_score, build_calibration_df, build_lift_table


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PATH = EXPORT_DIR / "analytic_dataset.csv"


def safe_roc_auc(y_true, y_prob) -> float | None:
    try:
        return float(roc_auc_score(y_true, y_prob))
    except Exception:
        return None


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DATASET_PATH}. Ejecuta primero: python -m scripts.export_dataset"
        )

    df = pd.read_csv(DATASET_PATH)
    df = clean_dataset(df)

    X, y = get_feature_matrix(df)

    numeric_features = [
        "signal_urgency",
        "signal_authority",
        "signal_reward",
        "signal_personalization",
    ]
    categorical_features = [
        "age_bracket",
        "gender",
        "education",
    ]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    if len(df) < 10 or y.nunique() < 2:
        pipeline.fit(X, y)
        y_pred = pipeline.predict(X)
        y_prob = pipeline.predict_proba(X)[:, 1]

        metrics = {
            "mode": "train_only_small_sample",
            "n_rows": int(len(df)),
            "clicked_positive_cases": int(y.sum()),
            "accuracy": float(accuracy_score(y, y_pred)),
            "precision": float(precision_score(y, y_pred, zero_division=0)),
            "recall": float(recall_score(y, y_pred, zero_division=0)),
            "f1": float(f1_score(y, y_pred, zero_division=0)),
            "roc_auc": safe_roc_auc(y, y_prob),
            "brier_score": safe_brier_score(y, y_prob),
            "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
        }

        result_df = df.copy()
        result_df["pred_clicked_flag"] = y_pred
        result_df["pred_clicked_prob"] = y_prob

        calibration_df = build_calibration_df(y, y_prob, n_bins=5)
        lift_df = build_lift_table(y, y_prob, n_bins=5)

    else:
        X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
            X, y, df, test_size=0.3, random_state=42, stratify=y
        )

        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "mode": "train_test_split",
            "n_rows": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "clicked_positive_cases_total": int(y.sum()),
            "clicked_positive_cases_test": int(y_test.sum()),
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": safe_roc_auc(y_test, y_prob),
            "brier_score": safe_brier_score(y_test, y_prob),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

        result_df = df_test.copy()
        result_df["pred_clicked_flag"] = y_pred
        result_df["pred_clicked_prob"] = y_prob

        calibration_df = build_calibration_df(y_test, y_prob, n_bins=10)
        lift_df = build_lift_table(y_test, y_prob, n_bins=10)

    fitted_preprocessor = pipeline.named_steps["preprocessor"]
    fitted_model = pipeline.named_steps["model"]

    feature_names = fitted_preprocessor.get_feature_names_out()
    coef_df = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": fitted_model.coef_[0],
            "abs_coefficient": abs(fitted_model.coef_[0]),
        }
    ).sort_values("abs_coefficient", ascending=False)

    metrics_path = MODEL_DIR / "baseline_logreg_metrics.json"
    coef_path = MODEL_DIR / "baseline_logreg_coefficients.csv"
    pred_path = MODEL_DIR / "baseline_logreg_predictions.csv"
    model_path = MODEL_DIR / "baseline_logreg_pipeline.joblib"
    calibration_path = MODEL_DIR / "baseline_logreg_calibration.csv"
    lift_path = MODEL_DIR / "baseline_logreg_lift.csv"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    coef_df.to_csv(coef_path, index=False, encoding="utf-8")
    result_df.to_csv(pred_path, index=False, encoding="utf-8")
    calibration_df.to_csv(calibration_path, index=False, encoding="utf-8")
    lift_df.to_csv(lift_path, index=False, encoding="utf-8")
    joblib.dump(pipeline, model_path)

    print("Modelo baseline entrenado/exportado correctamente.")
    print(f"Métricas: {metrics_path.resolve()}")
    print(f"Coeficientes: {coef_path.resolve()}")
    print(f"Predicciones: {pred_path.resolve()}")
    print(f"Calibración: {calibration_path.resolve()}")
    print(f"Lift: {lift_path.resolve()}")
    print(f"Modelo: {model_path.resolve()}")


if __name__ == "__main__":
    main()