from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Link, LanguageEnum
import secrets
import string
import re

def generate_random_token(length=12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

async def create_link(session: AsyncSession, user_id: int, slug: str = None, expires_at=None) -> Link | None:
    # Check limit (TODO in a real app)

    token = generate_random_token()

    # Validate slug
    if slug:
        if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
            return None
        # Check unique slug
        stmt = select(Link).where(Link.slug == slug)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return None

    link = Link(
        user_id=user_id,
        token=token,
        slug=slug,
        expires_at=expires_at
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link

async def get_link_by_token_or_slug(session: AsyncSession, identifier: str) -> Link | None:
    stmt = select(Link).where((Link.token == identifier) | (Link.slug == identifier))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_links(session: AsyncSession, user_id: int) -> list[Link]:
    stmt = select(Link).where(Link.user_id == user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def revoke_link(session: AsyncSession, user_id: int, link_id: int) -> bool:
    stmt = select(Link).where((Link.id == link_id) & (Link.user_id == user_id))
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()

    if link:
        link.is_active = False
        await session.commit()
        return True
    return False
