import pytest

from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "/health" in resp.get_json()["endpoints"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


def test_status(client):
    data = client.get("/api/status").get_json()
    assert data["status"] == "running"
    assert data["total_requests"] >= 1


def test_greet(client):
    resp = client.get("/api/greet/devops")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Hello, devops!"


@pytest.mark.parametrize(
    "op,a,b,expected",
    [("add", 2, 3, 5), ("subtract", 10, 4, 6), ("multiply", 4, 5, 20), ("divide", 9, 3, 3)],
)
def test_calculate(client, op, a, b, expected):
    resp = client.post("/api/calculate", json={"a": a, "b": b, "operation": op})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == expected


def test_calculate_divide_by_zero(client):
    resp = client.post("/api/calculate", json={"a": 1, "b": 0, "operation": "divide"})
    assert resp.status_code == 400


def test_calculate_unknown_operation(client):
    resp = client.post("/api/calculate", json={"a": 1, "b": 2, "operation": "pow"})
    assert resp.status_code == 400


def test_calculate_missing_field(client):
    resp = client.post("/api/calculate", json={"a": 1})
    assert resp.status_code == 400


def test_calculate_not_a_number(client):
    resp = client.post("/api/calculate", json={"a": "x", "b": 2})
    assert resp.status_code == 400


def test_calculate_requires_json(client):
    resp = client.post("/api/calculate", data="not json")
    assert resp.status_code == 400


def test_unknown_route_returns_json_404(client):
    resp = client.get("/nope")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not found"
