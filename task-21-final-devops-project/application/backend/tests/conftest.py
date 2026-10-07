import os

# Must be set before the app package is imported.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def task(client):
    response = client.post("/api/tasks", json={"title": "Write Helm chart", "priority": "HIGH"})
    assert response.status_code == 201
    return response.json()
