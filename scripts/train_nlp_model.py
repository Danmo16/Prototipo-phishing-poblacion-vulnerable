# scripts/train_nlp_model.py
from __future__ import annotations

import sys
import os
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Importar torch primero para evitar conflictos de DLL en Windows
import torch

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)


EXPORT_DIR = Path("data/exports")
MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATASET_PATH = EXPORT_DIR / "nlp_dataset.csv"
DEFAULT_MODEL_NAME = "distilbert-base-uncased"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrena un modelo NLP basado en DistilBERT usando GPU.")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--output-prefix", type=str, default="nlp_distilbert_gpu")
    parser.add_argument("--model-name", type=str, default=DEFAULT_MODEL_NAME)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=192)
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = torch.softmax(torch.tensor(logits), dim=1).numpy()[:, 1]
    preds = np.argmax(logits, axis=1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        preds,
        average="binary",
        zero_division=0,
    )

    metrics = {
        "accuracy": float(accuracy_score(labels, preds)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }

    try:
        metrics["roc_auc"] = float(roc_auc_score(labels, probs))
    except Exception:
        metrics["roc_auc"] = None

    return metrics


def main():
    args = parse_args()

    print("=== Entrenamiento NLP en GPU ===")
    print(f"Dataset: {args.dataset}")
    print(f"Modelo base: {args.model_name}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA disponible: {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        raise RuntimeError(
            "PyTorch no detecta CUDA en este proceso. "
            "Primero hay que resolver eso antes de entrenar en GPU."
        )

    print(f"GPU detectada: {torch.cuda.get_device_name(0)}")

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"No existe {dataset_path}. Ejecuta primero: python -m scripts.export_nlp_dataset"
        )

    df = pd.read_csv(dataset_path)
    df["text_input"] = df["text_input"].fillna("").astype(str)
    df["clicked_flag"] = df["clicked_flag"].fillna(0).astype(int)

    if len(df) < 20 or df["clicked_flag"].nunique() < 2:
        raise ValueError(
            "No hay suficientes datos para entrenar el modelo NLP. "
            "Se requieren al menos 20 filas y dos clases en clicked_flag."
        )

    train_df, test_df = train_test_split(
        df,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=df["clicked_flag"],
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_function(examples):
        return tokenizer(
            examples["text_input"],
            truncation=True,
            padding="max_length",
            max_length=args.max_length,
        )

    train_dataset = Dataset.from_pandas(
        train_df[["text_input", "clicked_flag"]].rename(columns={"clicked_flag": "label"})
    )
    test_dataset = Dataset.from_pandas(
        test_df[["text_input", "clicked_flag"]].rename(columns={"clicked_flag": "label"})
    )

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)

    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    test_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=2,
    )

    output_dir = MODEL_DIR / f"{args.output_prefix}_hf"

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=2,
        report_to="none",
        fp16=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    trainer.train()

    eval_metrics = trainer.evaluate()

    predictions = trainer.predict(test_dataset)
    logits = predictions.predictions
    probs = torch.softmax(torch.tensor(logits), dim=1).numpy()[:, 1]
    preds = np.argmax(logits, axis=1)

    pred_df = test_df.copy()
    pred_df["nlp_pred_clicked_flag"] = preds
    pred_df["nlp_pred_clicked_prob"] = probs

    metrics = {
        "model": "distilbert_sequence_classifier",
        "model_name": args.model_name,
        "device": "cuda",
        "dataset_path": str(dataset_path.resolve()),
        "output_prefix": args.output_prefix,
        "n_rows": int(len(df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "positive_cases_total": int(df["clicked_flag"].sum()),
        "accuracy": eval_metrics.get("eval_accuracy"),
        "precision": eval_metrics.get("eval_precision"),
        "recall": eval_metrics.get("eval_recall"),
        "f1": eval_metrics.get("eval_f1"),
        "roc_auc": eval_metrics.get("eval_roc_auc"),
    }

    metrics_path = MODEL_DIR / f"{args.output_prefix}_metrics.json"
    pred_path = MODEL_DIR / f"{args.output_prefix}_predictions.csv"
    model_path = MODEL_DIR / f"{args.output_prefix}_saved_model"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    pred_df.to_csv(pred_path, index=False, encoding="utf-8")
    trainer.save_model(str(model_path))
    tokenizer.save_pretrained(str(model_path))

    print("Modelo NLP entrenado/exportado correctamente.")
    print(f"Métricas: {metrics_path.resolve()}")
    print(f"Predicciones: {pred_path.resolve()}")
    print(f"Modelo guardado en: {model_path.resolve()}")


if __name__ == "__main__":
    main()