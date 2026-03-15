# ml/preprocessing.py
from __future__ import annotations

import pandas as pd


FEATURE_COLUMNS = [
    "signal_urgency",
    "signal_authority",
    "signal_reward",
    "signal_personalization",
    "age_bracket",
    "gender",
    "education",
]


TARGET_COLUMN = "clicked_flag"


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el dataset mínimo para modelado.
    """
    out = df.copy()

    # Normalización de texto en variables categóricas
    for col in ["age_bracket", "gender", "education", "template_name", "template_subject"]:
        if col in out.columns:
            out[col] = out[col].fillna("unknown").astype(str)

    # Variables numéricas binarias esperadas
    for col in ["signal_urgency", "signal_authority", "signal_reward", "signal_personalization"]:
        if col in out.columns:
            out[col] = out[col].fillna(0).astype(int)

    if TARGET_COLUMN in out.columns:
        out[TARGET_COLUMN] = out[TARGET_COLUMN].fillna(0).astype(int)

    return out


def get_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Devuelve X e y usando las columnas definidas.
    """
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y