from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.artifacts.infrastructure import log_model
from app.train.core import train_model
from utils.logger import get_logger


logger = get_logger(__name__)
DATASET_DIR = Path("storage/datasets")
DATASET_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = Path("storage/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def train_workflow(
    dataset_name: str,
) -> Path:
    """Load training data by name and delegate to the core training routine."""

    dataset_path = DATASET_DIR / f"{dataset_name}.parquet"
    if not dataset_path.exists():
        raise ValueError(f"Dataset '{dataset_name}' not found")

    df = pd.read_parquet(dataset_path)
    logger.info("Training dataset %s loaded from %s with shape %s", dataset_name, dataset_path, df.shape)

    model_path = train_model(df, output_dir=MODEL_DIR)
    model_name = model_path.stem
    timestamp = datetime.now(UTC)

    try:
        log_model(name=model_name, dataset_name=dataset_name, timestamp=timestamp)
    except Exception as e:
        logger.warning("Failed to log model to database: %s", e)

    return model_path
