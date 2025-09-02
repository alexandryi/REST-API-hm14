import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date

from src.main import app
from src.auth import get_current_user
from src.models import User
from src.database import AsyncSessionLocal

pytest_plugins = ("pytest_asyncio",)


async def override_get_current_user():
    return User(id=1, email="test@example.com", hashed_password="fake", is_verified=True)

app.dependency_overrides[get_current_user] = override_get_current_user

contact_id = None


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_user():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            existing = await session.get(User, 1)
            if not existing:
                user = User(
                    id=1,
                    email="test@example.com",
                    hashed_password="fake",
                    is_verified=True
                )
                session.add(user)


@pytest.mark.asyncio
async def test_create_contact():
    global contact_id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/contacts/",
            json={
                "first_name": "API",
                "last_name": "User",
                "email": "api@example.com",
                "phone": "123456789",
                "birthday": str(date(2000, 1, 1)),
                "extra_info": "Test contact"
            }
        )
    assert response.status_code in (200, 201)
    data = response.json()
    contact_id = data["id"]
    assert data["first_name"] == "API"
    assert data["email"] == "api@example.com"


@pytest.mark.asyncio
async def test_get_contacts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["id"] == contact_id for c in data)


@pytest.mark.asyncio
async def test_get_single_contact():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/contacts/{contact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["email"] == "api@example.com"


@pytest.mark.asyncio
async def test_update_contact():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put(
            f"/contacts/{contact_id}",
            json={
                "first_name": "Updated",
                "last_name": "User",
                "phone": "987654321"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["phone"] == "987654321"


@pytest.mark.asyncio
async def test_search_contacts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/contacts/search/?query=Updated")
    assert response.status_code == 200
    data = response.json()
    assert any(c["first_name"] == "Updated" for c in data)


@pytest.mark.asyncio
async def test_get_birthdays():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/contacts/birthdays/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_contact():
    global contact_id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete(f"/contacts/{contact_id}")
    assert response.status_code == 204

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_check = await ac.get(f"/contacts/{contact_id}")
    assert res_check.status_code == 404
