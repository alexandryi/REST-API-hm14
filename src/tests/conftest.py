import os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from src.database import Base, get_db
from src.main import app
from src.models import User
from src.auth import get_current_user


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:melnyk2006@localhost:5432/db_contacts_fin"
)

test_engine = create_async_engine(DATABASE_URL, echo=True, future=True)
TestingSessionLocal = sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    """Перед кожним тестом — чиста БД"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def seed_user(session):
    """Додає тестового користувача перед кожним тестом"""
    from src.models import User

    user = User(id=1, email="test@example.com", hashed_password="fake", is_verified=True)
    session.add(user)
    await session.commit()
    yield

    from sqlalchemy import text
    await session.execute(text("DELETE FROM contacts;"))
    await session.execute(text("DELETE FROM users;"))
    await session.commit()



@pytest_asyncio.fixture(scope="function")
async def session():
    """Окрема сесія для кожного тесту"""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def override_get_db(session):
    """Перевизначаємо залежність бази даних"""

    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(autouse=True)
async def override_current_user():
    """Фейковий користувач для тестів (без токенів)"""

    async def _fake_user():
        return User(id=1, email="test@example.com",
                    hashed_password="fake", is_verified=True)

    app.dependency_overrides[get_current_user] = _fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db):
    """HTTP-клієнт для тестів"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c
