from typing import Any, Dict, Optional

from sqlmodel import Session, select

from .models import AnalysisRecord, UsageLog, User


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def create_user(session: Session, email: str, plan: str = "free") -> User:
    user = User(email=email, plan=plan)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_or_create_user(session: Session, email: str) -> User:
    user = get_user_by_email(session, email)
    if user is None:
        user = create_user(session, email=email)
    return user


def create_usage_log(
    session: Session,
    *,
    event_type: str,
    payload: Dict[str, Any],
    user_id: Optional[int] = None,
) -> UsageLog:
    log = UsageLog(user_id=user_id, event_type=event_type, payload=payload)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def create_analysis_record(
    session: Session,
    *,
    analysis_type: str,
    record_count: int,
    details: Dict[str, Any],
    user_id: Optional[int] = None,
    target_name: Optional[str] = None,
    verdict: Optional[str] = None,
    confidence: Optional[float] = None,
) -> AnalysisRecord:
    record = AnalysisRecord(
        user_id=user_id,
        analysis_type=analysis_type,
        target_name=target_name,
        record_count=record_count,
        verdict=verdict,
        confidence=confidence,
        details=details,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
