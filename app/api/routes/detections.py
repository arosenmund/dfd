from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ... import crud
from ...models import User
from ...schemas.detections import DetectionRequest, DetectionResponse, RuleSchema
from ...services import detector
from .. import deps

router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("/check", response_model=DetectionResponse)
def run_detection(
    payload: DetectionRequest,
    db: Session = Depends(deps.get_db),
    user: Optional[User] = Depends(deps.get_current_user),
) -> DetectionResponse:
    try:
        result = detector.evaluate_detection(
            payload.real_summary, payload.fake_summary, payload.target_metadata
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    rule_payload = [rule.to_dict() for rule in result["rules"]]
    record = crud.create_analysis_record(
        db,
        analysis_type="detection",
        record_count=1,
        details={
            "rules": rule_payload,
            "triggered_reasons": result["findings"],
        },
        user_id=user.id if user else None,
        target_name=payload.target_name,
        verdict=result["verdict"],
        confidence=result["confidence"],
    )
    crud.create_usage_log(
        db,
        event_type="detections.check",
        payload={"detection_id": record.id, "verdict": result["verdict"]},
        user_id=user.id if user else None,
    )

    return DetectionResponse(
        detection_id=record.id,
        verdict=result["verdict"],
        confidence=result["confidence"],
        total_rules=result["total_rules"],
        triggered_rules=result["triggered_rules"],
        triggered_reasons=result["findings"],
        rules=[RuleSchema(**rule_dict) for rule_dict in rule_payload],
    )
