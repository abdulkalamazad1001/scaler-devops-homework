import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from alembic import command
from app.db import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def pytest_configure(config):
    # The session tears the schema down afterwards, so it must never point at the application database.
    if TEST_DATABASE_URL and TEST_DATABASE_URL == os.environ.get("DATABASE_URL"):
        pytest.exit("TEST_DATABASE_URL must not equal DATABASE_URL; use a dedicated test database", 2)


def migrate(connection, revision):
    # Built from the real migrations (not create_all) so every test run also exercises Alembic.
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    cfg.attributes["connection"] = connection
    if revision == "base":
        command.downgrade(cfg, revision)
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    else:
        command.upgrade(cfg, revision)
    connection.commit()


@pytest.fixture(scope="session")
def engine():
    # CI supplies a dedicated PostgreSQL database; local unit tests use isolated memory.
    url = TEST_DATABASE_URL or "sqlite://"
    options = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool} if url == "sqlite://" else {}
    )
    engine = create_engine(url, **options)
    if url == "sqlite://":
        # pysqlite skips BEGIN by default, which breaks per-test rollback and savepoints.
        @event.listens_for(engine, "connect")
        def autocommit_driver(dbapi_connection, _):
            dbapi_connection.isolation_level = None

        @event.listens_for(engine, "begin")
        def explicit_begin(connection):
            connection.exec_driver_sql("BEGIN")

    with engine.connect() as connection:
        migrate(connection, "head")
    try:
        yield engine
    finally:
        with engine.connect() as connection:
            migrate(connection, "base")
        engine.dispose()


@pytest.fixture()
def client(engine):
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
