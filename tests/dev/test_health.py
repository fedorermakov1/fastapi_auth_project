def test_health(client):
    response = client.get("/dev/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Healthy"
    }