import pytest
from jose import jwt

from app.config.settings import get_settings
from app.config.security import hash_password, verify_password
from app.database.models import User


def test_password_hashing():
    plain = "SuperSecret123!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)
    assert not verify_password("wrongpassword", hashed)


@pytest.mark.asyncio
async def test_user_creation(db_session):
    user = User(
        username="testuser",
        email="test@goldendome.local",
        hashed_password=hash_password("StrongPass123!"),
        role="soc_analyst",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"
    assert user.role == "soc_analyst"


@pytest.mark.asyncio
async def test_login_endpoint(client):
    # Seed user
    response = await client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@goldendome.local",
        "password": "StrongPass123!",
        "role": "soc_analyst",
    })
    assert response.status_code == 201, response.text

    response = await client.post("/api/auth/login", data={
        "username": "loginuser",
        "password": "StrongPass123!",
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post("/api/auth/login", data={
        "username": "nonexistent",
        "password": "wrong",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_public_registration_is_bootstrap_only_and_refresh_rotates_tokens(client):
    registration = await client.post("/api/auth/register", json={
        "username": "bootstrapadmin",
        "email": "bootstrapadmin@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    assert registration.status_code == 201

    second_registration = await client.post("/api/auth/register", json={
        "username": "attacker",
        "email": "attacker@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    assert second_registration.status_code == 403

    login = await client.post("/api/auth/login", data={"username": "bootstrapadmin", "password": "StrongPass123!"})
    assert login.status_code == 200
    refreshed = await client.post("/api/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != login.json()["access_token"]

    consumed_refresh = await client.post("/api/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert consumed_refresh.status_code == 401

    logout = await client.post("/api/auth/logout", json={"refresh_token": refreshed.json()["refresh_token"]})
    assert logout.status_code == 204
    revoked_refresh = await client.post("/api/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]})
    assert revoked_refresh.status_code == 401

    access_as_refresh = await client.post("/api/auth/refresh", json={"refresh_token": login.json()["access_token"]})
    assert access_as_refresh.status_code == 401


@pytest.mark.asyncio
async def test_malformed_access_token_is_rejected_without_server_error(client):
    settings = get_settings()
    token = jwt.encode({"sub": "not-an-id", "type": "access"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
