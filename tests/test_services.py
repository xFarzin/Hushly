import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base
from app.services.users import get_or_create_user, get_user_by_telegram_id
from app.services.links import create_link, get_link_by_token_or_slug
from app.services.messages import send_anonymous_message, get_message

# Setup in-memory sqlite for tests
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
async def test_user_creation(db_session):
    user = await get_or_create_user(db_session, 12345, "Test User")
    assert user.id is not None
    assert user.telegram_id == 12345
    assert user.display_name == "Test User"

    # Should get same user
    user2 = await get_or_create_user(db_session, 12345, "Another Name")
    assert user.id == user2.id

@pytest.mark.asyncio
async def test_link_creation(db_session):
    user = await get_or_create_user(db_session, 12345)
    link = await create_link(db_session, user.id, slug="my-custom-slug")

    assert link.id is not None
    assert link.token is not None
    assert link.slug == "my-custom-slug"

    found_link = await get_link_by_token_or_slug(db_session, "my-custom-slug")
    assert found_link.id == link.id

@pytest.mark.asyncio
async def test_send_anonymous_message(db_session):
    sender = await get_or_create_user(db_session, 111)
    receiver = await get_or_create_user(db_session, 222)
    link = await create_link(db_session, receiver.id)

    msg = await send_anonymous_message(db_session, sender.id, receiver.id, "Hello!", link.id)
    assert msg.id is not None
    assert msg.content == "Hello!"
    assert msg.receiver_id == receiver.id

    # Check conversation was created
    assert msg.conversation_id is not None

from app.services.users import update_display_name

@pytest.mark.asyncio
async def test_update_display_name(db_session):
    user = await get_or_create_user(db_session, 555)

    success = await update_display_name(db_session, user.id, "New Name")
    assert success is True

    updated_user = await get_or_create_user(db_session, 555)
    assert updated_user.display_name == "New Name"

    # Test invalid length
    long_name = "a" * 105
    success_fail = await update_display_name(db_session, user.id, long_name)
    assert success_fail is False

from app.bot.handlers.messaging import check_quick_replies
from app.models import QuickReply

@pytest.mark.asyncio
async def test_quick_replies_logic(db_session):
    user = await get_or_create_user(db_session, 777)

    qr1 = QuickReply(user_id=user.id, trigger="hello", response="hi there", match_mode="exact")
    qr2 = QuickReply(user_id=user.id, trigger="ugly", response="dont say that", match_mode="contains")
    db_session.add(qr1)
    db_session.add(qr2)
    await db_session.commit()

    # Test exact
    res = await check_quick_replies(db_session, user.id, "hello")
    assert res == "hi there"

    # Test contains
    res2 = await check_quick_replies(db_session, user.id, "you are ugly man")
    assert res2 == "dont say that"

    # Test no match
    res3 = await check_quick_replies(db_session, user.id, "something else")
    assert res3 is None
