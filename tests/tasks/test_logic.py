def test_read_tasks_with_fake_dependencies(
    client,
    fake_cache,
    fake_uow,
    fake_current_user,
):
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []
