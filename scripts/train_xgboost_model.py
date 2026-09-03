# scripts/train_xgboost_model.py
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

from xgboost import XGBClassifier

from ml.preprocessing import clean_dataset, get_feature_matrix
from ml.evaluation import safe_brier_score, build_calibration_df, build_lift_table

from scripts.artifact_utils import (
    build_timestamp,
    latest_versioned_or_legacy,
)


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATASET_PATH = EXPORT_DIR / "analytic_dataset_combined.csv"


def safe_roc_auc(y_true, y_prob) -> float | None:
    try:
        return float(roc_auc_score(y_true, y_prob))
    except Exception:
        return None


def build_preprocessor() -> ColumnTransformer:
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
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )


def extract_feature_importances(
    preprocessor: ColumnTransformer,
    model: XGBClassifier,
) -> pd.DataFrame:
    feature_names = preprocessor.get_feature_names_out()

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    return importance_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entrena un modelo XGBoost sobre el dataset analítico."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Ruta al CSV del dataset a usar.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="xgboost",
        help="Prefijo para los archivos exportados en data/models.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cpu", "cuda"],
        help="Dispositivo para entrenamiento de XGBoost.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Proporción del conjunto de prueba.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Semilla de aleatoriedad.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.dataset is None:
        dataset_path = latest_versioned_or_legacy(
            EXPORT_DIR,
            "analytic_dataset_combined_*.csv",
            "analytic_dataset_combined.csv",
        )

        if dataset_path is None:
            raise FileNotFoundError(
                "No se encontró ningún dataset combinado."
            )
    else:
        dataset_path = Path(args.dataset)

    run_id = build_timestamp()
    run_prefix = f"{args.output_prefix}_{run_id}"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"No existe {dataset_path}. "
            "Verifica la ruta o genera primero el dataset requerido."
        )

    df = pd.read_csv(dataset_path)
    df = clean_dataset(df)

    X, y = get_feature_matrix(df)

    if len(df) < 8 or y.nunique() < 2:
        raise ValueError(
            "No hay suficientes datos o clases para entrenar XGBoost. "
            "Necesitas al menos 8 observaciones y dos clases en clicked_flag."
        )

    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X,
        y,
        df,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    positive_cases = int(y_train.sum())
    negative_cases = int((y_train == 0).sum())
    scale_pos_weight = (negative_cases / positive_cases) if positive_cases > 0 else 1.0

    preprocessor = build_preprocessor()

    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)

    model = XGBClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=4,
        min_child_weight=2,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.5,
        reg_lambda=2.0,
        objective="binary:logistic",
        eval_metric=["logloss", "auc"],
        random_state=args.random_state,
        scale_pos_weight=scale_pos_weight,
        tree_method="hist",
        device=args.device,
        n_jobs=1,
    )

    model.fit(
        X_train_transformed,
        y_train,
        eval_set=[(X_test_transformed, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test_transformed)
    y_prob = model.predict_proba(X_test_transformed)[:, 1]

    metrics = {
        "model": "xgboost",
        "dataset_path": str(dataset_path.resolve()),
        "output_prefix": args.output_prefix,
        "run_id": run_id,
        "artifact_prefix": run_prefix,
        "device": args.device,
        "n_rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "positive_cases_total": int(y.sum()),
        "positive_cases_train": positive_cases,
        "positive_cases_test": int(y_test.sum()),
        "scale_pos_weight": float(scale_pos_weight),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": safe_roc_auc(y_test, y_prob),
        "brier_score": safe_brier_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    if "source" in df_test.columns:
        metrics["test_source_distribution"] = (
            df_test["source"].value_counts(dropna=False).to_dict()
        )

    result_df = df_test.copy()
    result_df["pred_clicked_flag"] = y_pred
    result_df["pred_clicked_prob"] = y_prob

    importance_df = extract_feature_importances(preprocessor, model)
    calibration_df = build_calibration_df(y_test, y_prob, n_bins=10)
    lift_df = build_lift_table(y_test, y_prob, n_bins=10)

    metrics_path = MODEL_DIR / f"{run_prefix}_metrics.json"
    importance_path = MODEL_DIR / f"{run_prefix}_feature_importances.csv"
    pred_path = MODEL_DIR / f"{run_prefix}_predictions.csv"
    model_path = MODEL_DIR / f"{run_prefix}_model.joblib"
    preprocessor_path = MODEL_DIR / f"{run_prefix}_preprocessor.joblib"
    calibration_path = MODEL_DIR / f"{run_prefix}_calibration.csv"
    lift_path = MODEL_DIR / f"{run_prefix}_lift.csv"

    print(f"Prefijo de ejecución: {run_prefix}")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    importance_df.to_csv(importance_path, index=False, encoding="utf-8")
    result_df.to_csv(pred_path, index=False, encoding="utf-8")
    calibration_df.to_csv(calibration_path, index=False, encoding="utf-8")
    lift_df.to_csv(lift_path, index=False, encoding="utf-8")
    joblib.dump(model, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    print("Modelo XGBoost entrenado/exportado correctamente.")
    print(f"Dataset usado: {dataset_path.resolve()}")
    print(f"Métricas: {metrics_path.resolve()}")
    print(f"Importancias: {importance_path.resolve()}")
    print(f"Predicciones: {pred_path.resolve()}")
    print(f"Calibración: {calibration_path.resolve()}")
    print(f"Lift: {lift_path.resolve()}")
    print(f"Modelo: {model_path.resolve()}")
    print(f"Preprocesador: {preprocessor_path.resolve()}")


if __name__ == "__main__":
    main()