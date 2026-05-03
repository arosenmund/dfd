from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class RuleSchema(BaseModel):
    field: str
    operator: str
    description: str
    threshold: Optional[float] = None
    value: Optional[Any] = None


class DetectionRequest(BaseModel):
    target_name: Optional[str] = Field(
        default=None,
        description="Optional label for the metadata being checked (e.g. filename).",
    )
    real_summary: Dict[str, Any]
    fake_summary: Dict[str, Any]
    target_metadata: Dict[str, Any]

    @validator("real_summary", "fake_summary", "target_metadata")
    def ensure_non_empty(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("summary data must not be empty")
        return value


class DetectionResponse(BaseModel):
    detection_id: int
    verdict: str
    confidence: float
    total_rules: int
    triggered_rules: int
    triggered_reasons: List[str]
    rules: List[RuleSchema]
