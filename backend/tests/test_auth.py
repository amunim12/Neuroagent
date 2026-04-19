import pytest
from httpx import AsyncClient

TEST_USER = {"email": "test@example.com", "password": "securepassword123"}


@pytest.mark.asyncio
async def test_register_returns_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post("/api/v1/auth/login", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post("/api/v1/auth/login", json={"email": TEST_USER["email"], "password": "wrongpassword"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    register_resp = await client.post("/api/v1/auth/register", json=TEST_USER)
    token = register_resp.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    # FastAPI < 0.118 returns 403 for missing HTTPBearer credentials; newer
    # versions return 401. Accept both so the suite works across the pinned range.
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert response.status_code == 401
