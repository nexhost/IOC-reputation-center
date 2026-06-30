from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceResult(BaseModel):
    source: str
    result: str
    score: int = Field(ge=0, le=100)
    evidence: dict[str, Any] = Field(default_factory=dict)
    online: bool = True


class IOCQuery(BaseModel):
    value: str = Field(min_length=3, max_length=2048)
    analyst: str = "Analista SOC"


class IOCResponse(BaseModel):
    id: int
    ioc_type: str
    ioc_value: str
    verdict: str
    risk_score: int
    source_results: list[SourceResult]
    created_at: datetime


class CaseCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    description: str = ""
    status: str = "Abierto"
    analyst_notes: str = ""


class ReportResponse(BaseModel):
    id: int
    report_path: str
    created_at: datetime
