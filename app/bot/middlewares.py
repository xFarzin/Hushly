from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.database import AsyncSessionLocal
from app.services.users import get_or_create_user
from app.security import rate_limiter
from app.config import settings

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data['db'] = session
            return await handler(event, data)

class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        db = data['db']
        user = None
        if event.from_user:
            user = await get_or_create_user(db, event.from_user.id, event.from_user.first_name)
            data['user'] = user
        return await handler(event, data)

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('user')
        if not user:
            return await handler(event, data)

        action = "message" if isinstance(event, Message) else "callback"
        limit = settings.message_rate_limit

        if rate_limiter.is_rate_limited(user.id, action, limit):
            # Try to send rate limit message using i18n
            from app.localization import get_text
            msg = get_text(user.language, "rate_limited")
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            return

        return await handler(event, data)
