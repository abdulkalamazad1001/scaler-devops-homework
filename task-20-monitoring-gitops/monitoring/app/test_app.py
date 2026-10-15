import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        client.get("/free")
        yield client
        client.get("/free")


@pytest.mark.parametrize("route", ["/", "/health", "/ready", "/metrics"])
def test_service_routes(client, route):
    assert client.get(route).status_code == 200


@pytest.mark.parametrize("value", ["invalid", "", "-1", "1.5", "5001"])
def test_invalid_work_input(client, value):
    assert client.get("/work", query_string={"ms": value}).status_code == 400


@pytest.mark.parametrize("value", ["invalid", "", "-1", "1.5", "201"])
def test_invalid_allocation_input(client, value):
    assert client.get("/alloc", query_string={"mb": value}).status_code == 400


def test_zero_work(client):
    assert client.get("/work?ms=0").get_json()["burned_ms"] == 0


def test_memory_allocation_and_release(client):
    assert client.get("/alloc?mb=1").get_json()["held_mb"] == 1
    assert client.get("/alloc?mb=1").get_json()["held_mb"] == 2
    assert client.get("/free").get_json()["held_mb"] == 0


def test_intentional_failure_is_measured(client):
    assert client.get("/error").status_code == 500
    metrics = client.get("/metrics").get_data(as_text=True)
    assert 'path="/error",status="500"' in metrics
