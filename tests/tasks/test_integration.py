def test_read_tasks_with_valid_token(
        test_client,
        auth_token,
):
    response = test_client.get(
        "/tasks/",
        headers={
            "Authorization": f"Bearer {auth_token}",
        },
    )

    assert response.status_code == 200
