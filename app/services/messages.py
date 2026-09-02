from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Message, Conversation, Reaction
from app.services.links import generate_random_token

async def get_or_create_conversation(session: AsyncSession, sender_id: int, receiver_id: int, link_id: int = None) -> Conversation:
    stmt = select(Conversation).where(
        (Conversation.sender_id == sender_id) & (Conversation.receiver_id == receiver_id)
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()

    if not conv:
        token = generate_random_token(16)
        conv = Conversation(
            token=token,
            sender_id=sender_id,
            receiver_id=receiver_id,
            link_id=link_id
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

    return conv

async def send_anonymous_message(session: AsyncSession, sender_id: int, receiver_id: int, content: str, link_id: int = None) -> Message:
    conv = await get_or_create_conversation(session, sender_id, receiver_id, link_id)

    msg = Message(
        conversation_id=conv.id,
        receiver_id=receiver_id,
        content=content
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg

async def get_message(session: AsyncSession, message_id: int) -> Message | None:
    stmt = select(Message).where(Message.id == message_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def add_reaction(session: AsyncSession, message_id: int, reactor_id: int, emoji: str) -> bool:
    msg = await get_message(session, message_id)
    if not msg:
        return False

    # Prevent duplicate reaction from same user on same message
    stmt = select(Reaction).where((Reaction.message_id == message_id) & (Reaction.reactor_id == reactor_id))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.emoji = emoji # update
    else:
        reaction = Reaction(
            message_id=message_id,
            reactor_id=reactor_id,
            emoji=emoji
        )
        session.add(reaction)

    await session.commit()
    return True
