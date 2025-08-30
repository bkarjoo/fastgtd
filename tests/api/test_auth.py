
from httpx import AsyncClient


async def test_signup(client: AsyncClient, override_get_db):
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()


async def test_signup_existing_email(client: AsyncClient, override_get_db):
    # First signup
    await client.post(
        "/auth/signup",
        json={
            "email": "existing@example.com",
            "password": "testpassword",
            "full_name": "Existing User",
        },
    )
    # Try to signup again with the same email
    response = await client.post(
        "/auth/signup",
        json={
            "email": "existing@example.com",
            "password": "anotherpassword",
            "full_name": "Another User",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "email_already_registered"


async def test_login(client: AsyncClient, override_get_db):
    # First signup a user
    await client.post(
        "/auth/signup",
        json={
            "email": "login@example.com",
            "password": "loginpassword",
            "full_name": "Login User",
        },
    )
    # Then try to login
    response = await client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "loginpassword",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_invalid_credentials(client: AsyncClient, override_get_db):
    response = await client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


async def test_me(client: AsyncClient, override_get_db):
    # Signup a user
    signup_response = await client.post(
        "/auth/signup",
        json={
            "email": "me@example.com",
            "password": "mepassword",
            "full_name": "Me User",
        },
    )
    user_id = signup_response.json()["id"]

    # Login to get a token
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "me@example.com",
            "password": "mepassword",
        },
    )
    token = login_response.json()["access_token"]

    # Access /me endpoint with the token
    response = await client.get(
        "/auth/me", headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["id"] == user_id


async def test_me_unauthorized(client: AsyncClient, override_get_db):
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
