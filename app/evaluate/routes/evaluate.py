from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from pathlib import Path

from app.artifacts.infrastructure.celery_app import celery_app
from app.artifacts.service.tasks import evaluate_model_task
from app.evaluate.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    EvaluateStatusResponse,
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/evaluate", tags=["Model Evaluation"])

DATASET_DIR = Path("storage/datasets")
MODEL_DIR = Path("storage/models")


@router.post("/")
def evaluate_endpoint(request: EvaluateRequest) -> EvaluateResponse:
    """
    Submit an evaluation job. Returns immediately with a task ID.
    Use GET /evaluate/status/{task_id} to check progress.
    """
    # Validate artifacts exist before submitting task
    model_path = MODEL_DIR / f"{request.model_name}.pkl"
    dataset_path = DATASET_DIR / f"{request.dataset_name}.parquet"
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model '{request.model_name}' not found")
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_name}' not found")
    
    # Submit async task
    task = evaluate_model_task.delay(request.model_name, request.dataset_name)
    logger.info("Submitted evaluation task %s for model %s on dataset %s", task.id, request.model_name, request.dataset_name)
    
    return EvaluateResponse(
        task_id=task.id,
        status="submitted",
        model_name=request.model_name,
        dataset_name=request.dataset_name,
    )


@router.get("/status/{task_id}")
def evaluate_status(task_id: str) -> EvaluateStatusResponse:
    """
    Check the status of an evaluation task.
    
    Status values:
    - PENDING: Task is waiting to be processed
    - STARTED: Task is currently running
    - SUCCESS: Task completed successfully (result contains auc)
    - FAILURE: Task failed
    """
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == "PENDING":
        return EvaluateStatusResponse(task_id=task_id, status="PENDING")
    elif result.state == "PROGRESS":
        return EvaluateStatusResponse(
            task_id=task_id,
            status="STARTED",
            result=result.info if isinstance(result.info, dict) else None,
        )
    elif result.state == "SUCCESS":
        return EvaluateStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            result=result.result,
        )
    else:  # FAILURE or other states
        return EvaluateStatusResponse(
            task_id=task_id,
            status="FAILURE",
            error=str(result.info) if result.info else "Unknown error",
        )
