def test_read_tasks_unauthorized(client):
    response = client.get("/tasks/")

    assert response.status_code == 401

def test_read_tasks_invalid_token(client):
    response = client.get(
        "/tasks/",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401