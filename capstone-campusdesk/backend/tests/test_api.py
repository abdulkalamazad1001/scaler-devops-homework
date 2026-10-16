import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import database_url, get_db
from app.main import app, latency, requests


def test_health_ready_metrics(client):
    assert client.get("/health").json()["status"] == "healthy"
    assert client.get("/ready").status_code == 200
    assert "campusdesk_http_requests_total" in client.get("/metrics").text


def test_crud(client, payload):
    created = client.post("/api/tickets", json=payload)
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert client.get(f"/api/tickets/{ticket_id}").json()["title"] == payload["title"]
    payload.update(status="resolved", assignee="IT Support")
    assert client.put(f"/api/tickets/{ticket_id}", json=payload).json()["status"] == "resolved"
    assert client.delete(f"/api/tickets/{ticket_id}").status_code == 204
    assert client.get(f"/api/tickets/{ticket_id}").status_code == 404


def test_filters_and_stats(client, payload):
    client.post("/api/tickets", json=payload)
    client.post("/api/tickets", json={**payload, "title": "Printer toner", "status": "resolved"})
    assert len(client.get("/api/tickets?status=open").json()) == 1
    assert len(client.get("/api/tickets?q=toner").json()) == 1
    assert len(client.get("/api/tickets?limit=1&offset=1").json()) == 1
    assert client.get("/api/stats").json() == {
        "total": 2,
        "open": 1,
        "in_progress": 0,
        "resolved": 1,
        "urgent": 1,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", " "),
        ("requester", ""),
        ("priority", "critical"),
        ("status", "closed"),
        ("category", "invalid"),
        ("location", "A"),
        ("unknown", "extra"),
    ],
)
def test_validation(client, payload, field, value):
    assert client.post("/api/tickets", json={**payload, field: value}).status_code == 422


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_ticket(client, payload, method):
    kwargs = {"json": payload} if method == "put" else {}
    assert getattr(client, method)("/api/tickets/99999", **kwargs).status_code == 404


def test_invalid_query(client):
    assert client.get("/api/tickets?limit=0").status_code == 422
    assert client.get("/api/tickets?status=anything").status_code == 422


def test_search_escapes_wildcards(client, payload):
    client.post("/api/tickets", json=payload)
    assert client.get("/api/tickets?q=%25").json() == []


def test_readiness_failure(client):
    class Unavailable:
        def execute(self, query):
            raise OperationalError("SELECT", {}, Exception("offline"))

    app.dependency_overrides[get_db] = lambda: Unavailable()
    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200


def test_unhandled_failure_is_counted(client):
    class Unavailable:
        def scalars(self, query):
            raise OperationalError("SELECT", {}, Exception("offline"))

    app.dependency_overrides[get_db] = lambda: Unavailable()
    counter = requests.labels("GET", "/api/tickets", "500")
    histogram = latency.labels("GET", "/api/tickets")
    before_count = counter._value.get()
    before_latency = histogram._sum.get()
    with pytest.raises(OperationalError):
        client.get("/api/tickets")
    assert counter._value.get() == before_count + 1
    assert histogram._sum.get() > before_latency


def test_metrics_use_bounded_routes_and_exclude_scrapes(client, payload):
    ticket_id = client.post("/api/tickets", json=payload).json()["id"]
    counter = requests.labels("GET", "/api/tickets/{ticket_id}", "200")
    before = counter._value.get()
    client.get(f"/api/tickets/{ticket_id}")
    assert counter._value.get() == before + 1
    output = client.get("/metrics").text
    assert f'route="/api/tickets/{ticket_id}"' not in output
    assert 'route="/metrics"' not in output


def test_invalid_update_preserves_existing_ticket(client, payload):
    ticket_id = client.post("/api/tickets", json=payload).json()["id"]
    assert client.put(f"/api/tickets/{ticket_id}", json={**payload, "title": " "}).status_code == 422
    assert client.get(f"/api/tickets/{ticket_id}").json()["title"] == payload["title"]


def test_pagination_has_stable_order(client, payload):
    ids = [client.post("/api/tickets", json={**payload, "title": f"Ticket {i}"}).json()["id"]
           for i in range(15)]
    first = client.get("/api/tickets?limit=13").json()
    second = client.get("/api/tickets?limit=13&offset=12").json()
    assert [row["id"] for row in first[:12]] + [row["id"] for row in second] == ids[::-1]


@pytest.mark.parametrize("ticket_id", [0, -1, 2_147_483_648, 10**20])
@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_out_of_range_ticket_id(client, payload, method, ticket_id):
    kwargs = {"json": payload} if method == "put" else {}
    assert getattr(client, method)(f"/api/tickets/{ticket_id}", **kwargs).status_code == 422


@pytest.mark.parametrize("field", ["title", "description", "requester", "location", "assignee"])
def test_nul_in_body_is_rejected(client, payload, field):
    response = client.post("/api/tickets", json={**payload, field: "Bad\x00value"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


def test_nul_in_search_and_large_offset_are_rejected(client):
    assert client.get("/api/tickets", params={"q": "a\x00b"}).status_code == 422
    assert client.get("/api/tickets?offset=2147483648").status_code == 422
    assert client.get("/api/tickets?offset=2147483647").status_code == 200


def test_write_failure_returns_503_and_rolls_back(client, payload, monkeypatch):
    def fail(self):
        raise OperationalError("COMMIT", {}, Exception("offline"))

    monkeypatch.setattr(Session, "commit", fail)
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 503
    assert "not saved" in response.json()["detail"]
    monkeypatch.undo()
    assert client.get("/api/tickets").json() == []


def test_missing_database_url_fails_clearly(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        database_url()
