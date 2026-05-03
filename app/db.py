from contextlib import contextmanager
from typing import Iterator

from sqlmodel import SQLModel, Session, create_engine

from .core.config import settings


def _build_engine_url() -> str:
    return settings.database_url


def _engine_connect_args() -> dict:
    database_url = settings.database_url
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def get_engine():
    return create_engine(_build_engine_url(), echo=False, connect_args=_engine_connect_args())


engine = get_engine()


def init_db() -> None:
    """Create database tables if they do not exist."""

    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    with Session(engine) as session:
        yield session
