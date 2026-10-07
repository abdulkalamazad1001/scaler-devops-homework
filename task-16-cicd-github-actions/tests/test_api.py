import pytest

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_reports_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    body = client.get("/").get_json()
    assert body["service"] == "cicd-demo"
    assert body["version"] == "1.2.3"
    assert body["secret_configured"] is False


def test_index_never_returns_secret_value(client, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s3cr3t")
    resp = client.get("/")
    assert resp.get_json()["secret_configured"] is True
    assert b"s3cr3t" not in resp.data


@pytest.mark.parametrize(
    "op,a,b,expected",
    [
        ("add", 2, 3, 5),
        ("subtract", 10, 4, 6),
        ("multiply", 6, 7, 42),
        ("divide", 10, 4, 2.5),
    ],
)
def test_operations(client, op, a, b, expected):
    resp = client.get(f"/api/{op}?a={a}&b={b}")
    assert resp.status_code == 200
    assert resp.get_json()["result"] == expected


def test_divide_by_zero_returns_400(client):
    resp = client.get("/api/divide?a=1&b=0")
    assert resp.status_code == 400
    assert "divide by zero" in resp.get_json()["error"]


def test_unknown_operation_returns_404(client):
    resp = client.get("/api/power?a=2&b=3")
    assert resp.status_code == 404


def test_missing_parameter_returns_400(client):
    resp = client.get("/api/add?a=1")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing query parameter b"


def test_non_numeric_parameter_returns_400(client):
    resp = client.get("/api/add?a=one&b=2")
    assert resp.status_code == 400
