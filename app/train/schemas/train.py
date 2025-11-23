from __future__ import annotations

from pydantic import BaseModel


class TrainRequest(BaseModel):
    dataset_name: str


class TrainResponse(BaseModel):
    task_id: str
    status: str = "submitted"
    dataset_name: str


class TrainStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None
