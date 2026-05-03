from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ... import crud
from ...models import User
from ...schemas.analysis import CollectionAnalysisRequest, CollectionAnalysisResponse
from ...services import collection_analysis
from .. import deps

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("/analyze", response_model=CollectionAnalysisResponse)
def analyze_collection(
    payload: CollectionAnalysisRequest,
    db: Session = Depends(deps.get_db),
    user: Optional[User] = Depends(deps.get_current_user),
) -> CollectionAnalysisResponse:
    try:
        summary = collection_analysis.analyze_records(payload.records)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    record = crud.create_analysis_record(
        db,
        analysis_type="collection",
        record_count=len(payload.records),
        details={"summary": summary, "dataset_name": payload.dataset_name},
        user_id=user.id if user else None,
        target_name=payload.dataset_name,
    )
    crud.create_usage_log(
        db,
        event_type="collections.analyze",
        payload={"analysis_id": record.id, "record_count": len(payload.records)},
        user_id=user.id if user else None,
    )

    return CollectionAnalysisResponse(
        analysis_id=record.id,
        dataset_name=payload.dataset_name,
        record_count=len(payload.records),
        summary=summary,
    )
