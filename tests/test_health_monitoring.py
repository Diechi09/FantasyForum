def test_health_endpoints(client):
    live_resp = client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.get_json()["status"] == "live"

    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.get_json()["status"] == "ready"


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "requests_by_endpoint" in data
    assert "responses_by_status" in data
    assert "average_latency_seconds" in data
