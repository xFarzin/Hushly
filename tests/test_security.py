import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base
from datetime import timedelta
from app.security import create_callback_token, decode_callback_token, rate_limiter

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_valid_callback_token(db_session):
    data = {"action": "reply", "user_id": 123}
    token = await create_callback_token(db_session, data)
    decoded = await decode_callback_token(db_session, token)

    assert decoded is not None
    assert decoded["action"] == "reply"
    assert decoded["user_id"] == 123

@pytest.mark.asyncio
async def test_expired_callback_token(db_session):
    data = {"action": "reply"}
    token = await create_callback_token(db_session, data, expires_delta=timedelta(minutes=-1))
    decoded = await decode_callback_token(db_session, token)

    assert decoded is None

@pytest.mark.asyncio
async def test_tampered_callback_token(db_session):
    data = {"action": "block", "user_id": 123}
    token = await create_callback_token(db_session, data)

    tampered_token = token + "xyz"
    decoded = await decode_callback_token(db_session, tampered_token)
    assert decoded is None

def test_rate_limiter():
    user_id = 999
    action = "message"
    limit = 3

    assert rate_limiter.is_rate_limited(user_id, action, limit) is False
    assert rate_limiter.is_rate_limited(user_id, action, limit) is False
    assert rate_limiter.is_rate_limited(user_id, action, limit) is False
    assert rate_limiter.is_rate_limited(user_id, action, limit) is True
