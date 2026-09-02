from sqlalchemy import select, func
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Link, Message as DBMessage, Conversation
from app.bot.keyboards import get_main_menu
from app.localization import get_text
from app.services.links import create_link
from app.config import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: User, db: AsyncSession, command):
    args = command.args

    if args:
        # If there are args, they might be opening a link to send a message
        # Handled in messaging router
        pass
    else:
        text = get_text(user.language, "welcome")
        await message.answer(text, reply_markup=get_main_menu(user.language))

@router.message(F.text.in_(["🔗 لینک‌های من", "🔗 My Links"]))
async def my_links_handler(message: Message, user: User, db: AsyncSession):
    from app.services.links import get_user_links
    links = await get_user_links(db, user.id)

    if not links:
        await message.answer(get_text(user.language, "no_links"))

        # Create a default link
        link = await create_link(db, user.id)
        if link:
            t_url = f"https://t.me/HushlyChatBot?start={link.token}"
            w_url = f"{settings.web_base_url}/{link.token}"
            await message.answer(get_text(user.language, "link_created", telegram_url=t_url, web_url=w_url))
    else:
        for link in links:
            if link.is_active:
                t_url = f"https://t.me/HushlyChatBot?start={link.token}"
                w_url = f"{settings.web_base_url}/{link.token}"
                await message.answer(get_text(user.language, "link_created", telegram_url=t_url, web_url=w_url))

@router.message(F.text.in_(["📊 آمار", "📊 Statistics"]))
async def stats_handler(message: Message, user: User, db: AsyncSession):
    links_count = await db.scalar(select(func.count(Link.id)).where(Link.user_id == user.id))
    received_count = await db.scalar(select(func.count(DBMessage.id)).where(DBMessage.receiver_id == user.id))
    sent_count = await db.scalar(select(func.count(Conversation.id)).where(Conversation.sender_id == user.id))

    text = f"📊 آمار شما / Your Statistics:\n\nلینک‌ها / Links: {links_count}\nپیام‌های دریافتی / Received: {received_count}\nمکالمات شروع شده / Convos Started: {sent_count}"
    await message.answer(text)

@router.message(F.text.in_(["⚙️ تنظیمات", "⚙️ Settings"]))
async def settings_handler(message: Message, user: User, db: AsyncSession):
    text = (
        "⚙️ تنظیمات / Settings\n\n"
        "To change language, send: /lang fa OR /lang en\n"
        "To change display name, send: /name YourName\n"
        f"Current Language: {user.language}\n"
        f"Current Display Name: {user.display_name}"
    )
    await message.answer(text)

@router.message(F.text.startswith("/lang "))
async def change_lang_handler(message: Message, user: User, db: AsyncSession):
    lang = message.text.split(" ")[1].strip().lower()
    if lang in ["fa", "en"]:
        from app.services.users import update_user_language
        await update_user_language(db, user.id, lang)
        user.language = lang
        await message.answer(get_text(lang, "welcome"), reply_markup=get_main_menu(lang))

@router.message(F.text.startswith("/name "))
async def change_name_handler(message: Message, user: User, db: AsyncSession):
    name = message.text[6:].strip()
    from app.services.users import update_display_name
    success = await update_display_name(db, user.id, name)
    if success:
        await message.answer("Display name updated successfully! / نام نمایشی شما با موفقیت به روز شد.")
    else:
        await message.answer("Invalid name length. / طول نام نامعتبر است.")

@router.message(F.text.in_(["⚡ پاسخ‌های سریع", "⚡ Quick Replies"]))
async def quick_replies_menu(message: Message, user: User, db: AsyncSession):
    await message.answer("To add a quick reply, use:\n/add_qr [exact/contains] [trigger] | [response]\nExample: /add_qr exact hello | hi there")

@router.message(F.text.startswith("/add_qr "))
async def add_quick_reply(message: Message, user: User, db: AsyncSession):
    # Extremely basic parser for MVP
    try:
        parts = message.text[8:].split("|")
        config_part = parts[0].strip().split(" ", 1)
        match_mode = config_part[0].strip().lower()
        trigger = config_part[1].strip()
        response = parts[1].strip()

        if match_mode not in ["exact", "contains"]:
            raise ValueError()

        from app.models import QuickReply
        qr = QuickReply(user_id=user.id, trigger=trigger, response=response, match_mode=match_mode)
        db.add(qr)
        await db.commit()
        await message.answer("Quick reply added successfully.")
    except Exception:
        await message.answer("Invalid format. Use: /add_qr [exact/contains] [trigger] | [response]")

@router.message(F.text.startswith("/link "))
async def custom_link_handler(message: Message, user: User, db: AsyncSession):
    # Example: /link my_slug
    parts = message.text.split(" ")
    if len(parts) >= 2:
        slug = parts[1].strip()
        from app.services.links import create_link
        link = await create_link(db, user.id, slug=slug)
        if link:
            t_url = f"https://t.me/HushlyChatBot?start={link.token}"
            w_url = f"{settings.web_base_url}/{link.token}"
            await message.answer(f"Custom link created!\\nTelegram: {t_url}\\nWeb: {w_url}")
        else:
            await message.answer("Failed to create custom link. Slug might be invalid or taken.")

@router.message(F.text.startswith("/revoke "))
async def revoke_link_handler(message: Message, user: User, db: AsyncSession):
    # Example: /revoke 5
    parts = message.text.split(" ")
    if len(parts) >= 2 and parts[1].isdigit():
        link_id = int(parts[1])
        from app.services.links import revoke_link
        success = await revoke_link(db, user.id, link_id)
        if success:
            await message.answer(f"Link {link_id} revoked successfully.")
        else:
            await message.answer("Failed to revoke link. You might not own it.")
