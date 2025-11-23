from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.artifacts.models import (
    DatasetRecord,
    EvaluationRecord,
    ModelRecord,
    PrunedModelRecord,
    get_session_factory,
)
from settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)
SessionLocal = get_session_factory()

if settings.database_url.startswith("sqlite"):
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_session() -> Session:
    """Get database session."""
    return SessionLocal()


def log_dataset(name: str, rows: int, macro: dict[str, Any]) -> None:
    """Log dataset artifact to database."""
    session = get_session()
    try:
        record = DatasetRecord(
            name=name,
            rows=rows,
            macro=macro,
        )
        session.add(record)
        session.commit()
        logger.info("Logged dataset %s to database", name)
    except Exception as e:
        session.rollback()
        logger.error("Failed to log dataset %s: %s", name, e)
        raise
    finally:
        session.close()


def log_model(name: str, dataset_name: str, timestamp: datetime | None = None) -> None:
    """Log model artifact to database."""
    session = get_session()
    try:
        dataset = session.query(DatasetRecord).filter(DatasetRecord.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found in database")

        record = ModelRecord(
            name=name,
            dataset_id=dataset.id,
            created_at=timestamp or datetime.now(UTC),
        )
        session.add(record)
        session.commit()
        logger.info("Logged model %s to database", name)
    except Exception as e:
        session.rollback()
        logger.error("Failed to log model %s: %s", name, e)
        raise
    finally:
        session.close()


def log_evaluation(model_name: str, dataset_name: str, auc: float) -> None:
    """Log evaluation result to database."""
    session = get_session()
    try:
        model = session.query(ModelRecord).filter(ModelRecord.name == model_name).first()
        if not model:
            raise ValueError(f"Model '{model_name}' not found in database")

        dataset = session.query(DatasetRecord).filter(DatasetRecord.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found in database")

        record = EvaluationRecord(
            model_id=model.id,
            dataset_id=dataset.id,
            auc=auc,
        )
        session.add(record)
        session.commit()
        logger.info("Logged evaluation for model %s on dataset %s (AUC: %.4f)", model_name, dataset_name, auc)
    except Exception as e:
        session.rollback()
        logger.error("Failed to log evaluation: %s", e)
        raise
    finally:
        session.close()


def log_pruned_model(model_name: str, pruned_name: str) -> None:
    """Log pruned model artifact to database."""
    session = get_session()
    try:
        base_model = session.query(ModelRecord).filter(ModelRecord.name == model_name).first()
        if not base_model:
            raise ValueError(f"Model '{model_name}' not found in database")

        record = PrunedModelRecord(
            pruned_name=pruned_name,
            base_model_id=base_model.id,
        )
        session.add(record)
        session.commit()
        logger.info("Logged pruned model %s (base: %s) to database", pruned_name, model_name)
    except Exception as e:
        session.rollback()
        logger.error("Failed to log pruned model %s: %s", pruned_name, e)
        raise
    finally:
        session.close()

