from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models import User, Link, Message as DBMessage, Conversation
from app.services.users import is_admin
from app.localization import get_text
from app.config import settings
import json

router = Router()

async def check_admin(user: User, db: AsyncSession) -> bool:
    is_super = user.telegram_id in settings.super_admins
    has_role = await is_admin(db, user.id)
    return is_super or has_role

@router.message(Command("admin"))
async def cmd_admin(message: Message, user: User, db: AsyncSession):
    if not await check_admin(user, db):
        return

    users_count = await db.scalar(select(func.count(User.id)))
    msgs_count = await db.scalar(select(func.count(DBMessage.id)))
    links_count = await db.scalar(select(func.count(Link.id)))

    dashboard = (
        "👑 Admin Dashboard 👑\n\n"
        f"Total Users: {users_count}\n"
        f"Total Messages: {msgs_count}\n"
        f"Active Links: {links_count}\n\n"
        "Commands:\n"
        "/ban [user_id]\n"
        "/unban [user_id]\n"
        "/broadcast [message]\n"
        "/db_stats"
    )
    await message.answer(dashboard)

@router.message(Command("ban"))
async def cmd_ban(message: Message, user: User, db: AsyncSession, command):
    if not await check_admin(user, db): return
    args = command.args
    if args and args.isdigit():
        target_id = int(args)
        stmt = update(User).where(User.id == target_id).values(is_banned=True)
        await db.execute(stmt)
        await db.commit()
        await message.answer(f"User {target_id} banned.")

@router.message(Command("unban"))
async def cmd_unban(message: Message, user: User, db: AsyncSession, command):
    if not await check_admin(user, db): return
    args = command.args
    if args and args.isdigit():
        target_id = int(args)
        stmt = update(User).where(User.id == target_id).values(is_banned=False)
        await db.execute(stmt)
        await db.commit()
        await message.answer(f"User {target_id} unbanned.")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, user: User, db: AsyncSession, command):
    if not await check_admin(user, db): return
    args = command.args
    if args:
        # In MVP, just mock it. In production, this goes to APScheduler/Celery queue
        await message.answer(f"Broadcast queued: {args[:50]}...")

@router.message(Command("db_stats"))
async def cmd_db_stats(message: Message, user: User, db: AsyncSession):
    if not await check_admin(user, db): return

    # Safe database inspection
    stats = {
        "users": await db.scalar(select(func.count(User.id))),
        "links": await db.scalar(select(func.count(Link.id))),
        "messages": await db.scalar(select(func.count(DBMessage.id))),
        "conversations": await db.scalar(select(func.count(Conversation.id)))
    }
    await message.answer(f"Database Stats:\n```json\n{json.dumps(stats, indent=2)}\n```", parse_mode="MarkdownV2")
