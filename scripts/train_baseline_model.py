from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from scripts.artifact_utils import (
    build_timestamp,
    latest_versioned_or_legacy,
)


TARGET_COLUMN = "clicked_flag"

NUMERIC_FEATURES = [
    "signal_urgency",
    "signal_authority",
    "signal_reward",
    "signal_personalization",
]

CATEGORICAL_FEATURES = [
    "age_bracket",
    "gender",
    "education",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Entrena una regresión logística baseline sobre el "
            "dataset analítico combinado."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help=("Ruta del dataset combinado. Si no se especifica, "
              "se utiliza automáticamente la versión más reciente."
             ),
    )

    parser.add_argument(
        "--output-prefix",
        type=str,
        default="baseline_logreg_combined",
        help="Prefijo para los artefactos de salida.",
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.30,
        help="Proporción destinada al conjunto de prueba.",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Semilla utilizada para dividir los datos.",
    )

    parser.add_argument(
        "--class-weight",
        choices=["balanced", "none"],
        default="balanced",
        help="Tratamiento del desbalance de clases.",
    )

    return parser.parse_args()


def convert_target(series: pd.Series) -> pd.Series:
    """Convierte la variable objetivo a valores enteros 0 y 1."""

    if pd.api.types.is_bool_dtype(series):
        return series.astype(int)

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype("Int64")

    normalized = series.astype(str).str.strip().str.lower()

    mapping = {
        "true": 1,
        "false": 0,
        "yes": 1,
        "no": 0,
        "sí": 1,
        "si": 1,
        "1": 1,
        "0": 0,
    }

    return normalized.map(mapping).astype("Int64")


def validate_dataset(dataframe: pd.DataFrame) -> None:
    required_columns = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing_columns = sorted(required_columns - set(dataframe.columns))

    if missing_columns:
        raise ValueError(
            "El dataset no contiene todas las columnas requeridas. "
            f"Faltan: {missing_columns}"
        )


def safe_roc_auc(y_true: pd.Series, probabilities: np.ndarray) -> float | None:
    if y_true.nunique() < 2:
        return None

    return float(roc_auc_score(y_true, probabilities))


def to_serializable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    return value


def main() -> None:
    args = parse_arguments()

    export_directory = Path("data/exports")

    if args.dataset is None:
        args.dataset = latest_versioned_or_legacy(
            export_directory,
            "analytic_dataset_combined_*.csv",
            "analytic_dataset_combined.csv",
        )

    if args.dataset is None:
        raise FileNotFoundError(
            "No se encontró ningún dataset combinado."
        )

    if not args.dataset.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset: {args.dataset.resolve()}"
        )

    dataframe = pd.read_csv(args.dataset)
    validate_dataset(dataframe)
    run_id = build_timestamp()
    run_prefix = f"{args.output_prefix}_{run_id}"

    # Conserva un identificador para relacionar predicciones con las filas.
    dataframe = dataframe.reset_index(drop=False).rename(
        columns={"index": "dataset_row_id"}
    )

    dataframe[TARGET_COLUMN] = convert_target(dataframe[TARGET_COLUMN])
    dataframe = dataframe.dropna(subset=[TARGET_COLUMN]).copy()
    dataframe[TARGET_COLUMN] = dataframe[TARGET_COLUMN].astype(int)

    # Normalización mínima de variables.
    for column in NUMERIC_FEATURES:
        dataframe[column] = (
            pd.to_numeric(dataframe[column], errors="coerce")
            .fillna(0)
            .astype(float)
        )

    for column in CATEGORICAL_FEATURES:
        dataframe[column] = (
            dataframe[column]
            .fillna("unknown")
            .astype(str)
            .str.strip()
        )

    if dataframe[TARGET_COLUMN].nunique() < 2:
        raise ValueError(
            "La variable clicked_flag debe contener las clases 0 y 1."
        )

    X = dataframe[FEATURE_COLUMNS]
    y = dataframe[TARGET_COLUMN]

    # División estratificada.
    train_indices, test_indices = train_test_split(
        np.arange(len(dataframe)),
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    X_train = X.iloc[train_indices]
    X_test = X.iloc[test_indices]
    y_train = y.iloc[train_indices]
    y_test = y.iloc[test_indices]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                "passthrough",
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    class_weight = (
        "balanced"
        if args.class_weight == "balanced"
        else None
    )

    classifier = LogisticRegression(
        solver="liblinear",
        max_iter=2000,
        class_weight=class_weight,
        random_state=args.random_state,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    pipeline.fit(X_train, y_train)

    predicted_class = pipeline.predict(X_test)
    predicted_probability = pipeline.predict_proba(X_test)[:, 1]

    matrix = confusion_matrix(
        y_test,
        predicted_class,
        labels=[0, 1],
    )

    metrics = {
        "model": "baseline_logistic_regression",
        "dataset_path": str(args.dataset.resolve()),
        "output_prefix": args.output_prefix,
        "run_id": run_id,
        "artifact_prefix": run_prefix,
        "target": TARGET_COLUMN,
        "features": FEATURE_COLUMNS,
        "class_weight": args.class_weight,
        "random_state": args.random_state,
        "test_size": args.test_size,
        "n_rows": int(len(dataframe)),
        "train_rows": int(len(train_indices)),
        "test_rows": int(len(test_indices)),
        "positive_cases_total": int(y.sum()),
        "positive_cases_train": int(y_train.sum()),
        "positive_cases_test": int(y_test.sum()),
        "accuracy": float(
            accuracy_score(y_test, predicted_class)
        ),
        "precision": float(
            precision_score(
                y_test,
                predicted_class,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_test,
                predicted_class,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_test,
                predicted_class,
                zero_division=0,
            )
        ),
        "roc_auc": safe_roc_auc(
            y_test,
            predicted_probability,
        ),
        "brier_score": float(
            brier_score_loss(
                y_test,
                predicted_probability,
            )
        ),
        "confusion_matrix": {
            "true_negative": int(matrix[0, 0]),
            "false_positive": int(matrix[0, 1]),
            "false_negative": int(matrix[1, 0]),
            "true_positive": int(matrix[1, 1]),
        },
    }

    output_directory = Path("data/models")
    output_directory.mkdir(parents=True, exist_ok=True)

    metrics_path = (
        output_directory
        / f"{run_prefix}_metrics.json"
    )

    predictions_path = (
        output_directory
        / f"{run_prefix}_predictions.csv"
    )

    coefficients_path = (
        output_directory
        / f"{run_prefix}_coefficients.csv"
    )

    calibration_path = (
        output_directory
        / f"{run_prefix}_calibration.csv"
    )

    model_path = (
        output_directory
        / f"{run_prefix}_model.joblib"
    )

    split_path = (
        output_directory
        / f"{run_prefix}_split.csv"
    )

    print(f"Prefijo de ejecución: {run_prefix}")

    # Guardar métricas.
    with metrics_path.open("w", encoding="utf-8") as file:
        json.dump(
            metrics,
            file,
            indent=2,
            ensure_ascii=False,
            default=to_serializable,
        )

    # Guardar predicciones con columnas de contexto disponibles.
    context_columns = [
        column
        for column in [
            "dataset_row_id",
            "source",
            "campaign_id",
            "template_id",
            "segment_id",
            "target_id",
            "age_bracket",
            "gender",
            "education",
        ]
        if column in dataframe.columns
    ]

    predictions = dataframe.iloc[test_indices][context_columns].copy()
    predictions["clicked_flag"] = y_test.to_numpy()
    predictions["baseline_pred_clicked_flag"] = predicted_class
    predictions["baseline_pred_probability"] = predicted_probability
    predictions.to_csv(predictions_path, index=False)

    # Guardar coeficientes.
    feature_names = (
        pipeline.named_steps["preprocessor"]
        .get_feature_names_out()
    )

    coefficients = pipeline.named_steps[
        "classifier"
    ].coef_[0]

    coefficients_dataframe = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "abs_coefficient": np.abs(coefficients),
        }
    ).sort_values(
        by="abs_coefficient",
        ascending=False,
    )

    coefficients_dataframe.to_csv(
        coefficients_path,
        index=False,
    )

    # Guardar curva de calibración.
    probability_true, probability_predicted = calibration_curve(
        y_test,
        predicted_probability,
        n_bins=10,
        strategy="quantile",
    )

    calibration_dataframe = pd.DataFrame(
        {
            "mean_predicted_probability": probability_predicted,
            "fraction_of_positives": probability_true,
        }
    )

    calibration_dataframe.to_csv(
        calibration_path,
        index=False,
    )

    # Guardar asignación de filas a train/test.
    split_dataframe = dataframe[
        ["dataset_row_id"]
        + (["source"] if "source" in dataframe.columns else [])
    ].copy()

    split_dataframe["split"] = "unused"
    split_dataframe.loc[train_indices, "split"] = "train"
    split_dataframe.loc[test_indices, "split"] = "test"
    split_dataframe.to_csv(split_path, index=False)

    # Guardar pipeline completo.
    joblib.dump(pipeline, model_path)

    print("Entrenamiento completado correctamente.")
    print(f"Dataset: {args.dataset}")
    print(f"Filas totales: {len(dataframe)}")
    print(f"Entrenamiento: {len(train_indices)}")
    print(f"Prueba: {len(test_indices)}")
    print(f"Casos positivos: {int(y.sum())}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"ROC-AUC: {metrics['roc_auc']}")
    print(f"Brier score: {metrics['brier_score']:.4f}")
    print(f"Métricas guardadas en: {metrics_path}")
    print(f"Predicciones guardadas en: {predictions_path}")
    print(f"Coeficientes guardados en: {coefficients_path}")
    print(f"Modelo guardado en: {model_path}")


if __name__ == "__main__":
    main()