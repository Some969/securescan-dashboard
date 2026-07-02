from typing import Any, Dict, List, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]


class ScanRequest(BaseModel):
    target_url: str = Field(..., min_length=3, max_length=500, examples=["https://example.com"])


class Finding(BaseModel):
    title: str
    description: str
    severity: Severity
    affected_component: str
    recommendation: str


class ScanSummary(BaseModel):
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int


class ScanHistoryItem(BaseModel):
    id: int
    target_url: str
    scan_date: datetime
    risk_score: int
    grade: str
    total_findings: int

    class Config:
        from_attributes = True


class ScanReport(BaseModel):
    id: int
    target_url: str
    scan_date: datetime
    risk_score: int
    grade: str
    summary: ScanSummary
    checks: Dict[str, Any]
    findings: List[Finding]
    recommendations: List[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DeleteResponse(BaseModel):
    message: str
