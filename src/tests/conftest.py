import os
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models import User
from src.auth import get_current_user


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:melnyk2006@localhost:5432/db_contacts_fin")

test_engine = create_async_engine(DATABASE_URL, echo=True, future=True)
TestingSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    """Окремий цикл подій для pytest-asyncio"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Створює таблиці перед тестами і дропає після"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def session():
    """Окрема сесія для кожного тесту"""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def override_get_db(session):
    """Перевизначення залежності бази даних"""

    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(autouse=True)
async def override_current_user():
    """Завжди повертаємо фейкового юзера замість справжньої перевірки токена"""
    async def _fake_user():
        return User(id=1, email="test@example.com", hashed_password="fake", is_verified=True)

    app.dependency_overrides[get_current_user] = _fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db):
    """Фікстура http-клієнта"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
