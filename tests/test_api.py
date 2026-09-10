def test_health_endpoint(normal_client):
    data = normal_client.get("/api/v1/health").json()
    assert data["status"] == "ok" and data["demo_mode"] is False
    assert data["is_demo"] is False
    assert data["services"]["authenticity_detector"] == "unavailable"


def test_normal_session_uses_unavailable_adapters(normal_client):
    response = normal_client.post("/api/v1/sessions", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["is_demo"] is False
    assert data["authenticity"]["status"] == "unavailable"
    assert data["conversation"]["status"] == "unavailable"
    assert data["risk"]["level"] == "unavailable"


def test_no_normal_to_demo_fallback(normal_client):
    response = normal_client.post("/api/v1/sessions", json={"scenario": "safe_human"})
    assert response.status_code == 400


def test_session_creation_and_demo_labelling(demo_client):
    response = demo_client.post("/api/v1/sessions", json={"scenario": "safe_human"})
    assert response.status_code == 201
    data = response.json()
    assert all(data[k]["is_demo"] for k in ("caller", "authenticity", "conversation", "risk"))
    manager = demo_client.app.state.manager
    events = manager.records[data["session_id"]].events
    assert events
    assert all(event.is_demo is True for event in events)
    assert all(event.payload.get("is_demo", True) is True for event in events)


def test_demo_health_labels_fixture_services(demo_client):
    data = demo_client.get("/api/v1/health").json()
    assert data["demo_mode"] is True
    assert data["is_demo"] is True
    assert data["services"]["authenticity_detector"] == "ready"


def test_protection_activation(demo_client):
    sid = demo_client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = demo_client.post(f"/api/v1/sessions/{sid}/enable")
    assert response.status_code == 200 and response.json()["protection_state"] == "active"


def test_call_end_cleanup_state(demo_client):
    sid = demo_client.post("/api/v1/sessions", json={}).json()["session_id"]
    data = demo_client.post(f"/api/v1/sessions/{sid}/end").json()
    assert data["call_state"] == "ended" and data["protection_state"] == "stopped"


def test_registered_commands_cannot_be_overridden_by_query_parameter(demo_client):
    session_id = demo_client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = demo_client.post(f"/api/v1/sessions/{session_id}/enable?command=end&cmd=end")
    data = response.json()
    assert data["protection_state"] == "active"
    assert data["call_state"] == "created"
