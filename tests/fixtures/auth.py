import pytest_asyncio


@pytest_asyncio.fixture
async def auth_token(async_client, test_user):
    response = await async_client.post(
        "/token",
        data={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_auth_token(async_client, admin_user):
    response = await async_client.post(
        "/token",
        data={
            "username": "admin_user",
            "password": "admin_password",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]