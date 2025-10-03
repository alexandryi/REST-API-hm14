import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date

from src.main import app

pytest_plugins = ("pytest_asyncio",)

contact_id = None


@pytest.fixture(scope="function", autouse=True)
async def setup_test_data(override_get_db, override_current_user):
    """Налаштування тестових даних для кожного тесту"""
    yield


@pytest.mark.asyncio
async def test_create_contact(client):
    global contact_id
    response = await client.post(
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
async def test_get_contacts(client):
    response = await client.get("/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["id"] == contact_id for c in data)


@pytest.mark.asyncio
async def test_get_single_contact(client):
    response = await client.get(f"/contacts/{contact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["email"] == "api@example.com"


@pytest.mark.asyncio
async def test_update_contact(client):
    response = await client.put(
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
async def test_search_contacts(client):
    response = await client.get("/contacts/search/?query=Updated")
    assert response.status_code == 200
    data = response.json()
    assert any(c["first_name"] == "Updated" for c in data)


@pytest.mark.asyncio
async def test_get_birthdays(client):
    response = await client.get("/contacts/birthdays/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_contact(client):
    global contact_id
    response = await client.delete(f"/contacts/{contact_id}")
    assert response.status_code == 204

    response_check = await client.get(f"/contacts/{contact_id}")
    assert response_check.status_code == 404