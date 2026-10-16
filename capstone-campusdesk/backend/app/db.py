import os
from functools import cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    # No silent fallback: a missing URL must not quietly create a throwaway local database.
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set; point it at the CampusDesk PostgreSQL database")
    return url


@cache
def get_engine() -> Engine:
    # Created on first use so importing the app (e.g. in tests) never needs a database.
    url = database_url()
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )


def __getattr__(name: str):
    # Keeps `from app.db import engine` (Helm schema wait) working without an import-time engine.
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db():
    with Session(get_engine()) as session:
        yield session
