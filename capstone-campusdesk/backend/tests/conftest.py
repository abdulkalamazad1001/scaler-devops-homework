import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # CI supplies a dedicated PostgreSQL database; local unit tests use isolated memory.
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    options = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool} if url == "sqlite://" else {}
    )
    engine = create_engine(url, **options)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()

    def override():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture()
def payload():
    return {
        "title": "Library Wi-Fi unavailable",
        "description": "Second floor access point",
        "requester": "Aisha Khan",
        "location": "Central library",
        "category": "network",
        "priority": "urgent",
        "status": "open",
        "assignee": "Unassigned",
    }
