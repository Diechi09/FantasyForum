def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_endpoint_trailing_slash(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_endpoint(client):
    client.get("/health")

    response = client.get("/metrics")

    body = response.data.decode()
    assert response.status_code == 200
    assert "http_requests_total" in body
    assert "http_request_latency_seconds" in body
