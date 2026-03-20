# scripts/compare_models.py
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
from sklearn.tree import DecisionTreeClassifier
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


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PATH = EXPORT_DIR / "analytic_dataset.csv"


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
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def evaluate_model(name: str, pipeline: Pipeline, X_train, X_test, y_train, y_test) -> tuple[dict, pd.DataFrame]:
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
    else:
        # fallback raro, por seguridad
        y_prob = y_pred.astype(float)

    metrics = {
        "model": name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": safe_roc_auc(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    pred_df = X_test.copy()
    pred_df["y_true"] = y_test.values
    pred_df["y_pred"] = y_pred
    pred_df["y_prob"] = y_prob
    pred_df["model"] = name

    return metrics, pred_df


def extract_logreg_coefficients(pipeline: Pipeline) -> pd.DataFrame:
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

    return coef_df


def extract_tree_importances(pipeline: Pipeline) -> pd.DataFrame:
    fitted_preprocessor = pipeline.named_steps["preprocessor"]
    fitted_model = pipeline.named_steps["model"]

    feature_names = fitted_preprocessor.get_feature_names_out()

    imp_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": fitted_model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    return imp_df


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DATASET_PATH}. Ejecuta primero: python -m scripts.export_dataset"
        )

    df = pd.read_csv(DATASET_PATH)
    df = clean_dataset(df)

    X, y = get_feature_matrix(df)

    if len(df) < 10 or y.nunique() < 2:
        raise ValueError(
            "No hay suficientes datos o clases para comparar modelos. "
            "Necesitas más observaciones y al menos dos clases en clicked_flag."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    # Regresión logística
    logreg_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    # Árbol de decisión simple
    tree_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "model",
                DecisionTreeClassifier(
                    max_depth=4,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    logreg_metrics, logreg_pred_df = evaluate_model(
        "logistic_regression",
        logreg_pipeline,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    tree_metrics, tree_pred_df = evaluate_model(
        "decision_tree",
        tree_pipeline,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    comparison_df = pd.DataFrame([logreg_metrics, tree_metrics])

    # coeficientes / importancias
    logreg_coef_df = extract_logreg_coefficients(logreg_pipeline)
    tree_imp_df = extract_tree_importances(tree_pipeline)

    # guardar modelos
    joblib.dump(logreg_pipeline, MODEL_DIR / "logreg_pipeline.joblib")
    joblib.dump(tree_pipeline, MODEL_DIR / "decision_tree_pipeline.joblib")

    # exportar métricas
    comparison_df.to_csv(MODEL_DIR / "model_comparison_metrics.csv", index=False, encoding="utf-8")
    logreg_coef_df.to_csv(MODEL_DIR / "logreg_coefficients.csv", index=False, encoding="utf-8")
    tree_imp_df.to_csv(MODEL_DIR / "decision_tree_importances.csv", index=False, encoding="utf-8")

    # exportar predicciones
    all_predictions = pd.concat([logreg_pred_df, tree_pred_df], ignore_index=True)
    all_predictions.to_csv(MODEL_DIR / "model_predictions.csv", index=False, encoding="utf-8")

    # json de resumen
    summary = {
        "n_rows_total": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "positive_cases_total": int(y.sum()),
        "models_compared": ["logistic_regression", "decision_tree"],
    }
    with open(MODEL_DIR / "model_comparison_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("Comparación de modelos exportada correctamente.")
    print(f"Métricas: {(MODEL_DIR / 'model_comparison_metrics.csv').resolve()}")
    print(f"Coeficientes logística: {(MODEL_DIR / 'logreg_coefficients.csv').resolve()}")
    print(f"Importancias árbol: {(MODEL_DIR / 'decision_tree_importances.csv').resolve()}")
    print(f"Predicciones: {(MODEL_DIR / 'model_predictions.csv').resolve()}")
    print(f"Resumen: {(MODEL_DIR / 'model_comparison_summary.json').resolve()}")


if __name__ == "__main__":
    main()