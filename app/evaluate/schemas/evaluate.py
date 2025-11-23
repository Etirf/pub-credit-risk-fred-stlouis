from __future__ import annotations

from pydantic import BaseModel


class EvaluateRequest(BaseModel):
    model_name: str
    dataset_name: str


class EvaluateResponse(BaseModel):
    task_id: str
    status: str = "submitted"
    model_name: str
    dataset_name: str


class EvaluateStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None
