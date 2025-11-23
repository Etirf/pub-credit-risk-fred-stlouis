from __future__ import annotations

from pydantic import BaseModel


class PruneRequest(BaseModel):
    model_name: str
    dataset_name: str


class PruneResponse(BaseModel):
    task_id: str
    status: str = "submitted"
    model_name: str
    dataset_name: str


class PruneStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None
