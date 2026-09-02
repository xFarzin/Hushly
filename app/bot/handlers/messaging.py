import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.localization import get_text
from app.services.links import get_link_by_token_or_slug
from app.services.messages import send_anonymous_message, add_reaction
from app.services.moderation import block_user, is_blocked, create_report
from app.services.users import get_user_by_id
from app.bot.keyboards import get_message_actions, get_reaction_keyboard
from app.security import decode_callback_token
from app.config import settings
from app.services.image_generation import generate_message_image
from aiogram.types import FSInputFile

router = Router()

class SendMessage(StatesGroup):
    waiting_for_message = State()
    link_id = State()
    receiver_id = State()

class ReplyMessage(StatesGroup):
    waiting_for_reply = State()
    conversation_id = State()
    sender_id = State() # the person we are replying to

from app.bot.keyboards import get_main_menu

@router.message(CommandStart())
async def cmd_start(message: Message, user: User, db: AsyncSession, state: FSMContext, command):
    args = command.args
    if args:
        link = await get_link_by_token_or_slug(db, args)
        if not link or not link.is_active:
            await message.answer(get_text(user.language, "invalid_token"))
            return

        await db.refresh(link, ['user'])
        receiver = link.user

        # Check block
        if await is_blocked(db, blocker_id=receiver.id, blocked_id=user.id):
            # Fail gracefully without exposing block status
            pass

        name = receiver.display_name or f"User {receiver.id}"
        await message.answer(get_text(user.language, "send_message_prompt", name=name))

        await state.update_data(link_id=link.id, receiver_id=receiver.id)
        await state.set_state(SendMessage.waiting_for_message)
    else:
        text = get_text(user.language, "welcome")
        await message.answer(text, reply_markup=get_main_menu(user.language))

@router.message(SendMessage.waiting_for_message)
async def process_anonymous_message(message: Message, user: User, db: AsyncSession, state: FSMContext, bot: Bot):
    if not message.text:
        return # Only text for MVP

    data = await state.get_data()
    receiver_id = data.get("receiver_id")
    link_id = data.get("link_id")

    if await is_blocked(db, blocker_id=receiver_id, blocked_id=user.id):
        # Fake success
        await message.answer(get_text(user.language, "message_sent"))
        await state.clear()
        return

    # Truncate
    content = message.text[:settings.max_message_length]

    msg = await send_anonymous_message(db, user.id, receiver_id, content, link_id)

    # Try to notify receiver
    receiver = await get_user_by_id(db, receiver_id)
    if receiver:
        try:
            kb = await get_message_actions(db, receiver.language, msg.id, user.id, msg.conversation_id)
            await bot.send_message(
                receiver.telegram_id,
                get_text(receiver.language, "message_received", content=content),
                reply_markup=kb
            )
            # Generate image version
            import os
            try:
                image_path = await asyncio.to_thread(generate_message_image, content)
                if image_path:
                    await bot.send_photo(receiver.telegram_id, FSInputFile(image_path))
                    os.remove(image_path)
            except Exception as img_e:
                print(f"Image generation failed: {img_e}")

            # Check Quick Replies
            qr_response = await check_quick_replies(db, receiver_id, content)
            if qr_response:
                # Send auto-reply back to the sender
                await bot.send_message(
                    user.telegram_id,
                    f"⚡ پاسخ خودکار / Auto-reply:\n\n{qr_response}"
                )

        except Exception as e:
            print(f"Failed to deliver: {e}")

    await message.answer(get_text(user.language, "message_sent"))
    await state.clear()

@router.callback_query()
async def process_callback(callback: CallbackQuery, user: User, db: AsyncSession, state: FSMContext, bot: Bot):
    payload = await decode_callback_token(db, callback.data)
    if not payload:
        await callback.answer(get_text(user.language, "error_occurred"), show_alert=True)
        return

    action = payload.get("a")

    if action == "reply":
        sender_id = payload.get("s")
        conv_id = payload.get("c")

        await state.update_data(sender_id=sender_id, conversation_id=conv_id)
        await state.set_state(ReplyMessage.waiting_for_reply)

        await callback.message.answer(get_text(user.language, "reply_prompt"))
        await callback.answer()

    elif action == "block":
        blocked_id = payload.get("u")
        await block_user(db, user.id, blocked_id)
        await callback.answer(get_text(user.language, "user_blocked"), show_alert=True)

    elif action == "report":
        reported_id = payload.get("u")
        msg_id = payload.get("m")
        await create_report(db, user.id, msg_id, reported_id, "Reported via inline button")
        await callback.answer(get_text(user.language, "message_reported"), show_alert=True)

    elif action == "react":
        msg_id = payload.get("m")
        kb = await get_reaction_keyboard(db, user.language, msg_id)
        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer()

    elif action == "do_react":
        msg_id = payload.get("m")
        emoji = payload.get("e")
        await add_reaction(db, msg_id, user.id, emoji)
        # Restore original kb
        # We need sender/conv id for the kb, which we don't have here easily unless we pack it or fetch from db.
        # For simplicity, just remove keyboard after reacting in MVP
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer(emoji)

@router.message(ReplyMessage.waiting_for_reply)
async def process_reply(message: Message, user: User, db: AsyncSession, state: FSMContext, bot: Bot):
    if not message.text:
        return

    data = await state.get_data()
    sender_id = data.get("sender_id")
    conv_id = data.get("conversation_id")

    content = message.text[:settings.max_message_length]

    # Save message in DB
    from app.models import Message as DBMessage
    msg = DBMessage(
        conversation_id=conv_id,
        receiver_id=sender_id,
        content=content
    )
    db.add(msg)
    await db.commit()

    # Notify original sender
    original_sender = await get_user_by_id(db, sender_id)
    if original_sender:
        try:
            # We don't expose receiver identity.
            name = user.display_name or "Someone"
            await bot.send_message(
                original_sender.telegram_id,
                f"پاسخ از طرف {name}:\n\n{content}" if original_sender.language == "fa" else f"Reply from {name}:\n\n{content}"
            )
        except Exception:
            pass

    await message.answer(get_text(user.language, "reply_sent"))
    await state.clear()

async def check_quick_replies(db: AsyncSession, receiver_id: int, message_text: str) -> str | None:
    from sqlalchemy import select
    from app.models import QuickReply

    stmt = select(QuickReply).where((QuickReply.user_id == receiver_id) & (QuickReply.is_active == True))
    result = await db.execute(stmt)
    replies = result.scalars().all()

    for qr in replies:
        if qr.match_mode == "exact" and message_text.strip().lower() == qr.trigger.lower():
            return qr.response
        elif qr.match_mode == "contains" and qr.trigger.lower() in message_text.lower():
            return qr.response

    return None
