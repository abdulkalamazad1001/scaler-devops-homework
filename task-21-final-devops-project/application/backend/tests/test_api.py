def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_root_reports_service_name(client):
    assert client.get("/").json()["service"] == "TaskBoard API"


def test_create_task(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Deploy application", "priority": "HIGH", "assignee": "Platform team"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Deploy application"
    assert body["status"] == "TODO"
    assert body["id"] > 0


def test_create_task_rejects_empty_title(client):
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422


def test_create_task_rejects_unknown_priority(client):
    assert client.post("/api/tasks", json={"title": "x", "priority": "URGENT"}).status_code == 422


def test_list_tasks_newest_first(client):
    client.post("/api/tasks", json={"title": "first"})
    client.post("/api/tasks", json={"title": "second"})
    titles = [t["title"] for t in client.get("/api/tasks").json()]
    assert titles == ["second", "first"]


def test_get_task(client, task):
    response = client.get(f"/api/tasks/{task['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Write Helm chart"


def test_get_missing_task_returns_404(client):
    assert client.get("/api/tasks/9999").status_code == 404


def test_update_task_status(client, task):
    response = client.put(f"/api/tasks/{task['id']}", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["priority"] == "HIGH"


def test_delete_task(client, task):
    assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert client.get(f"/api/tasks/{task['id']}").status_code == 404


def test_stats(client):
    client.post("/api/tasks", json={"title": "a"})
    client.post("/api/tasks", json={"title": "b", "status": "IN_PROGRESS"})
    client.post("/api/tasks", json={"title": "c", "status": "DONE"})
    assert client.get("/api/tasks/stats").json() == {"total": 3, "todo": 1, "inProgress": 1, "done": 1}


def test_metrics_endpoint_exposes_request_counter(client):
    client.get("/api/tasks")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert "taskboard_tasks_created_total" in body
