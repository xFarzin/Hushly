from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Block, Report

async def block_user(session: AsyncSession, blocker_id: int, blocked_id: int) -> bool:
    if blocker_id == blocked_id:
        return False

    stmt = select(Block).where((Block.blocker_id == blocker_id) & (Block.blocked_id == blocked_id))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        session.add(block)
        await session.commit()
        return True
    return False

async def is_blocked(session: AsyncSession, blocker_id: int, blocked_id: int) -> bool:
    stmt = select(Block).where((Block.blocker_id == blocker_id) & (Block.blocked_id == blocked_id))
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def create_report(session: AsyncSession, reporter_id: int, message_id: int, reported_user_id: int, reason: str) -> bool:
    report = Report(
        reporter_id=reporter_id,
        reported_message_id=message_id,
        reported_user_id=reported_user_id,
        reason=reason
    )
    session.add(report)
    await session.commit()
    return True
