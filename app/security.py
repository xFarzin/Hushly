from datetime import datetime, timedelta, timezone
from jose import jwt
from typing import Optional, Dict, Any
import json
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import CallbackToken
from app.config import settings

def _generate_random_token(length=32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

async def create_callback_token(session: AsyncSession, data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a stateful, DB-backed token to bypass Telegram's 64-byte limit"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=1)

    token = _generate_random_token(24) # 24 chars is well under 64 bytes

    cb_token = CallbackToken(
        token=token,
        payload=json.dumps(data),
        expires_at=expire
    )
    session.add(cb_token)
    await session.commit()

    return token

async def decode_callback_token(session: AsyncSession, token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a DB-backed callback token"""
    stmt = select(CallbackToken).where(
        (CallbackToken.token == token) &
        ((CallbackToken.expires_at > datetime.now(timezone.utc)) | (CallbackToken.expires_at == None))
    )
    result = await session.execute(stmt)
    cb_token = result.scalar_one_or_none()

    if cb_token:
        return json.loads(cb_token.payload)
    return None

# Simple in-memory rate limiter (bucket)
class RateLimiter:
    def __init__(self):
        self._requests = {}

    def is_rate_limited(self, user_id: int, action: str, limit_per_minute: int) -> bool:
        now = datetime.now(timezone.utc)
        key = f"{user_id}:{action}"

        if key not in self._requests:
            self._requests[key] = []

        # Clean up old requests
        self._requests[key] = [t for t in self._requests[key] if now - t < timedelta(minutes=1)]

        if len(self._requests[key]) >= limit_per_minute:
            return True

        self._requests[key].append(now)
        return False

rate_limiter = RateLimiter()
