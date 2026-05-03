from typing import AsyncGenerator, Optional

from fastapi import Depends, Header
from sqlmodel import Session

from .. import crud
from ..db import engine
from ..models import User


def get_db() -> AsyncGenerator[Session, None]:
    with Session(engine) as session:
        yield session


def get_current_user(
    db: Session = Depends(get_db),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Optional[User]:
    if not x_user_email:
        return None
    return crud.get_or_create_user(db, x_user_email)
