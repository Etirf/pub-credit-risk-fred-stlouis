from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.artifacts.service.tasks import train_model_task
from app.train.schemas import TrainRequest, TrainResponse, TrainStatusResponse
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/train", tags=["Model Training"])


@router.post("/")
def train_endpoint(request: TrainRequest) -> TrainResponse:
    """
    Submit a training job. Returns immediately with a task ID.
    Use GET /train/status/{task_id} to check progress.
    """
    # Validate dataset exists before submitting task
    from pathlib import Path
    
    dataset_path = Path("storage/datasets") / f"{request.dataset_name}.parquet"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_name}' not found")
    
    # Submit async task
    task = train_model_task.delay(request.dataset_name)
    logger.info("Submitted training task %s for dataset %s", task.id, request.dataset_name)
    
    return TrainResponse(
        task_id=task.id,
        status="submitted",
        dataset_name=request.dataset_name,
    )


@router.get("/status/{task_id}")
def train_status(task_id: str) -> TrainStatusResponse:
    """
    Check the status of a training task.
    
    Status values:
    - PENDING: Task is waiting to be processed
    - STARTED: Task is currently running
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed
    """
    from app.artifacts.infrastructure.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == "PENDING":
        return TrainStatusResponse(task_id=task_id, status="PENDING")
    elif result.state == "PROGRESS":
        return TrainStatusResponse(
            task_id=task_id,
            status="STARTED",
            result=result.info if isinstance(result.info, dict) else None,
        )
    elif result.state == "SUCCESS":
        return TrainStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            result=result.result,
        )
    else:  # FAILURE or other states
        return TrainStatusResponse(
            task_id=task_id,
            status="FAILURE",
            error=str(result.info) if result.info else "Unknown error",
        )
