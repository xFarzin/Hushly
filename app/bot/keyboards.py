from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from app.security import create_callback_token
from app.localization import get_text

def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text=get_text(lang, "messages")),
            KeyboardButton(text=get_text(lang, "my_links"))
        ],
        [
            KeyboardButton(text=get_text(lang, "statistics")),
            KeyboardButton(text=get_text(lang, "quick_replies"))
        ],
        [
            KeyboardButton(text=get_text(lang, "settings")),
            KeyboardButton(text=get_text(lang, "help"))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_message_actions(session: AsyncSession, lang: str, message_id: int, sender_id: int, conversation_id: int) -> InlineKeyboardMarkup:
    # Use DB tokens for callback data to avoid IDOR and stay under 64 bytes
    reply_token = await create_callback_token(session, {"a": "reply", "c": conversation_id, "s": sender_id})
    block_token = await create_callback_token(session, {"a": "block", "u": sender_id})
    report_token = await create_callback_token(session, {"a": "report", "m": message_id, "u": sender_id})
    react_token = await create_callback_token(session, {"a": "react", "m": message_id})

    kb = [
        [
            InlineKeyboardButton(text=get_text(lang, "reply_button"), callback_data=reply_token),
            InlineKeyboardButton(text=get_text(lang, "react_button"), callback_data=react_token)
        ],
        [
            InlineKeyboardButton(text=get_text(lang, "block_button"), callback_data=block_token),
            InlineKeyboardButton(text=get_text(lang, "report_button"), callback_data=report_token)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

async def get_reaction_keyboard(session: AsyncSession, lang: str, message_id: int) -> InlineKeyboardMarkup:
    emojis = ["❤️", "😂", "😍", "😢", "😡", "👍"]
    row = []
    for e in emojis:
        token = await create_callback_token(session, {"a": "do_react", "m": message_id, "e": e})
        row.append(InlineKeyboardButton(text=e, callback_data=token))

    return InlineKeyboardMarkup(inline_keyboard=[row])
