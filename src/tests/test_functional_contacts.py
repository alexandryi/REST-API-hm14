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
    await client.post("/contacts/", json={
        "first_name": "API",
        "last_name": "User",
        "email": "api@example.com",
        "phone": "123456789",
        "birthday": "2000-01-01",
        "extra_info": "Test"
    })

    response = await client.get("/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert any(c["email"] == "api@example.com" for c in data)



@pytest.mark.asyncio
async def test_get_single_contact(client):
    created = await client.post(
        "/contacts/",
        json={
            "first_name": "Single",
            "last_name": "User",
            "email": "single@example.com",
            "phone": "111222333",
            "birthday": "1999-09-09",
            "extra_info": "One record"
        }
    )
    contact_id = created.json()["id"]

    response = await client.get(f"/contacts/{contact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["email"] == "single@example.com"


@pytest.mark.asyncio
async def test_update_contact(client):
    created = await client.post(
        "/contacts/",
        json={
            "first_name": "Old",
            "last_name": "Name",
            "email": "update@example.com",
            "phone": "5555555",
            "birthday": "2001-01-01",
            "extra_info": "Before update"
        }
    )
    contact_id = created.json()["id"]

    response = await client.put(
        f"/contacts/{contact_id}",
        json={
            "first_name": "Updated",
            "last_name": "User",
            "phone": "9999999"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["phone"] == "9999999"


@pytest.mark.asyncio
async def test_search_contacts(client):
    await client.post(
        "/contacts/",
        json={
            "first_name": "Search",
            "last_name": "Target",
            "email": "search@example.com",
            "phone": "8888888",
            "birthday": "2002-02-02",
            "extra_info": "Find me"
        }
    )

    response = await client.get("/contacts/search/?query=Search")
    assert response.status_code == 200
    data = response.json()
    assert any(c["first_name"] == "Search" for c in data)
"""
@pytest.mark.asyncio
async def test_get_birthdays(client):
    response = await client.get("/contacts/birthdays/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

"""
@pytest.mark.asyncio
async def test_get_birthdays(client):
    await client.post(
        "/contacts/",
        json={
            "first_name": "Birthday",
            "last_name": "User",
            "email": "bday@example.com",
            "phone": "7777777",
            "birthday": str(date(2000, 1, 1)),
            "extra_info": "Birthday soon"
        }
    )

    response = await client.get("/contacts/birthdays/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)



@pytest.mark.asyncio
async def test_delete_contact(client):
    created = await client.post(
        "/contacts/",
        json={
            "first_name": "Delete",
            "last_name": "Me",
            "email": "delete@example.com",
            "phone": "6666666",
            "birthday": "2003-03-03",
            "extra_info": "Temporary contact"
        }
    )
    contact_id = created.json()["id"]

    response = await client.delete(f"/contacts/{contact_id}")
    assert response.status_code == 204

    check = await client.get(f"/contacts/{contact_id}")
    assert check.status_code == 404