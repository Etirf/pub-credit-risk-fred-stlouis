from __future__ import annotations

import pandas as pd
from pathlib import Path

from app.artifacts.infrastructure import log_evaluation
from app.evaluate.core import evaluate_model
from utils.logger import get_logger


logger = get_logger(__name__)
DATASET_DIR = Path("storage/datasets")
DATASET_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = Path("storage/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_workflow(model_name: str | None, dataset_name: str | None) -> float:
    """Evaluate a trained model on a dataset identified by name."""

    if not model_name or not dataset_name:
        raise ValueError("Missing model_name or dataset_name")

    model_path = MODEL_DIR / f"{model_name}.pkl"
    dataset_path = DATASET_DIR / f"{dataset_name}.parquet"

    if not model_path.exists():
        raise ValueError(f"Model '{model_name}' not found")
    if not dataset_path.exists():
        raise ValueError(f"Dataset '{dataset_name}' not found")

    df = pd.read_parquet(dataset_path)
    logger.info(
        "Evaluating model %s on dataset %s (shape %s)",
        model_name,
        dataset_name,
        df.shape,
    )
    auc = evaluate_model(df, model_path)

    try:
        log_evaluation(model_name=model_name, dataset_name=dataset_name, auc=auc)
    except Exception as e:
        logger.warning("Failed to log evaluation to database: %s", e)

    return auc
