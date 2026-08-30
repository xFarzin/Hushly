from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from app.database import AsyncSessionLocal
from app.models import Link, CallbackToken

async def cleanup_expired_links():
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        stmt = update(Link).where(
            (Link.expires_at != None) &
            (Link.expires_at < now) &
            (Link.is_active == True)
        ).values(is_active=False)

        await session.execute(stmt)
        await session.commit()

async def cleanup_expired_tokens():
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        stmt = delete(CallbackToken).where(
            (CallbackToken.expires_at != None) &
            (CallbackToken.expires_at < now)
        )

        await session.execute(stmt)
        await session.commit()
