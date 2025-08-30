import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.db.session import Base
import app.models # noqa: F401
from app.models.user import User # noqa: F401
from app.db.deps import get_db


@pytest.fixture(name="app_instance")
def app_instance_fixture():
    return create_app()


@pytest.fixture(name="client")
async def client_fixture(app_instance) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        yield client


@pytest.fixture(name="test_db_engine")
async def test_db_engine_fixture():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(name="test_db_session")
async def test_db_session_fixture(test_db_engine):
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="override_get_db")
async def override_get_db_fixture(app_instance, test_db_session):
    async def _get_test_db():
        yield test_db_session

    app_instance.dependency_overrides[get_db] = _get_test_db
    yield
    app_instance.dependency_overrides.clear()