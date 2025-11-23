from __future__ import annotations

from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class MacroOverrides(BaseModel):
    debt_ratio: Optional[float] = None
    delinquency: Optional[float] = None
    interest_rate: Optional[float] = None


class DatasetRequest(BaseModel):
    n_borrowers: int = 1000
    macro_overrides: Optional[MacroOverrides] = None


class DatasetResponse(BaseModel):
    dataset_name: str
    rows: int
    macro: Dict[str, float]
    preview: List[Dict[str, Any]]


__all__ = [
    "MacroOverrides",
    "DatasetRequest",
    "DatasetResponse",
]
