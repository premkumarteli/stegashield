"""Database engine, session factory, and dependency injection."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db.models import Base


def create_db_engine(db_url: str) -> Engine:
    """Create a configured SQLAlchemy engine according to the connection string dialect."""
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {
        "pool_pre_ping": True,
    }

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in db_url:
            engine_kwargs["poolclass"] = StaticPool
    else:
        # MySQL or PostgreSQL connection tuning
        engine_kwargs["pool_recycle"] = 3600
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20

    return create_engine(db_url, connect_args=connect_args, **engine_kwargs)


engine: Engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session with automatic lifecycle management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine: Engine | None = None) -> None:
    """Initialize all tables defined in Base metadata."""
    e = target_engine or engine
    Base.metadata.create_all(bind=e)
