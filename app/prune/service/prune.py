from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.artifacts.infrastructure import log_pruned_model
from app.prune.core import prune_model
from utils.logger import get_logger


logger = get_logger(__name__)
DATASET_DIR = Path("storage/datasets")
DATASET_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = Path("storage/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def prune_workflow(model_name: str | None, dataset_name: str | None) -> Path:
    """Run the feature pruning pipeline and return the new pruned model path."""

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
        "Pruning model %s using dataset %s (shape %s)",
        model_name,
        dataset_name,
        df.shape,
    )
    pruned_path = prune_model(df, model_path)
    pruned_name = pruned_path.stem

    try:
        log_pruned_model(model_name=model_name, pruned_name=pruned_name)
    except Exception as e:
        logger.warning("Failed to log pruned model to database: %s", e)

    return pruned_path
