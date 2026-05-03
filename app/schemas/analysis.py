from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class CollectionAnalysisRequest(BaseModel):
    dataset_name: Optional[str] = Field(
        default=None, description="Optional name to identify the analyzed collection."
    )
    records: List[Dict[str, Any]]

    @validator("records")
    def validate_records(cls, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not value:
            raise ValueError("records must contain at least one metadata entry")
        return value


class CollectionAnalysisResponse(BaseModel):
    analysis_id: int
    dataset_name: Optional[str]
    record_count: int
    summary: Dict[str, Any]
