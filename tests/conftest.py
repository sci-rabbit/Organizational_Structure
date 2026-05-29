import os

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

import models.department  # noqa: F401 — регистрирует модель в Base.metadata
import models.employee    # noqa: F401
from core.database import get_ro_session, get_rw_session
from main import app
from models.base import Base

TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/test_app_db",
)

engine = create_async_engine(TEST_URL, poolclass=NullPool)
session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="session")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db(create_tables):
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client(clean_db):
    async def override_rw():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_ro():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_rw_session] = override_rw
    app.dependency_overrides[get_ro_session] = override_ro

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
