from __future__ import annotations

from datetime import datetime
from typing import Any

from app.artifacts.infrastructure.celery_app import celery_app
from app.artifacts.infrastructure.repository import (
    log_dataset as sync_log_dataset,
    log_evaluation as sync_log_evaluation,
    log_model as sync_log_model,
    log_pruned_model as sync_log_pruned_model,
)
from app.evaluate.service import evaluate_workflow
from app.prune.service import prune_workflow
from app.train.service import train_workflow


@celery_app.task(name="artifacts.log_dataset")
def log_dataset_async(name: str, rows: int, macro: dict[str, Any]) -> dict[str, Any]:
    """Async task to log dataset to database."""
    sync_log_dataset(name=name, rows=rows, macro=macro)
    return {"status": "success", "artifact": "dataset", "name": name}


@celery_app.task(name="artifacts.log_model")
def log_model_async(name: str, dataset_name: str, timestamp: str | None = None) -> dict[str, Any]:
    """Async task to log model to database."""
    # Convert timestamp string back to datetime if provided
    dt = datetime.fromisoformat(timestamp) if timestamp else None
    sync_log_model(name=name, dataset_name=dataset_name, timestamp=dt)
    return {"status": "success", "artifact": "model", "name": name}


@celery_app.task(name="artifacts.log_evaluation")
def log_evaluation_async(model_name: str, dataset_name: str, auc: float) -> dict[str, Any]:
    """Async task to log evaluation to database."""
    sync_log_evaluation(model_name=model_name, dataset_name=dataset_name, auc=auc)
    return {"status": "success", "artifact": "evaluation", "model": model_name, "auc": auc}


@celery_app.task(name="artifacts.log_pruned_model")
def log_pruned_model_async(model_name: str, pruned_name: str) -> dict[str, Any]:
    """Async task to log pruned model to database."""
    sync_log_pruned_model(model_name=model_name, pruned_name=pruned_name)
    return {"status": "success", "artifact": "pruned_model", "name": pruned_name}


# ===========================================================================
# ML Operation Tasks (long-running async jobs)
# ============================================================================


@celery_app.task(name="ml.train_model", bind=True, max_retries=3)
def train_model_task(self, dataset_name: str) -> dict[str, Any]:
    """Async task to train a model on a dataset.
    
    Returns:
        dict with model_name, dataset_name, and status
    """
    try:
        model_path = train_workflow(dataset_name)
        model_name = model_path.stem
        return {
            "status": "success",
            "model_name": model_name,
            "dataset_name": dataset_name,
        }
    except ValueError:
        # Don't retry on validation errors (like "not found")
        # These are permanent errors, not transient failures
        raise
    except Exception as e:
        # Retry on transient errors (database connection, file I/O, etc.)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="ml.evaluate_model", bind=True, max_retries=3)
def evaluate_model_task(self, model_name: str, dataset_name: str) -> dict[str, Any]:
    """Async task to evaluate a model on a dataset.
    
    Returns:
        dict with model_name, dataset_name, auc, and status
    """
    try:
        auc = evaluate_workflow(model_name, dataset_name)
        return {
            "status": "success",
            "model_name": model_name,
            "dataset_name": dataset_name,
            "auc": auc,
        }
    except ValueError:
        # Don't retry on validation errors (like "not found")
        # These are permanent errors, not transient failures
        raise
    except Exception as e:
        # Retry on transient errors (database connection, file I/O, etc.)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="ml.prune_model", bind=True, max_retries=3)
def prune_model_task(self, model_name: str, dataset_name: str) -> dict[str, Any]:
    """Async task to prune a model.
    
    Returns:
        dict with model_name, pruned_model_name, dataset_name, and status
    """
    try:
        pruned_path = prune_workflow(model_name, dataset_name)
        pruned_name = pruned_path.stem
        return {
            "status": "success",
            "model_name": model_name,
            "pruned_model_name": pruned_name,
            "dataset_name": dataset_name,
        }
    except ValueError:
        # Don't retry on validation errors (like "not found")
        # These are permanent errors, not transient failures
        raise
    except Exception as e:
        # Retry on transient errors (database connection, file I/O, etc.)
        raise self.retry(exc=e, countdown=60)

