from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, AdminRole

async def get_or_create_user(session: AsyncSession, telegram_id: int, first_name: str = "") -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(telegram_id=telegram_id, display_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_language(session: AsyncSession, user_id: int, language: str) -> None:
    user = await get_user_by_id(session, user_id)
    if user:
        user.language = language
        await session.commit()

async def update_display_name(session: AsyncSession, user_id: int, name: str) -> bool:
    if len(name) > 100 or len(name.strip()) == 0:
        return False

    user = await get_user_by_id(session, user_id)
    if user:
        user.display_name = name.strip()
        await session.commit()
        return True
    return False

async def is_admin(session: AsyncSession, user_id: int) -> bool:
    stmt = select(AdminRole).where(AdminRole.user_id == user_id)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()
    return admin is not None
