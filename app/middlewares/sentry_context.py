from aiogram import BaseMiddleware
from app.utils.sentry import enrich_scope
from app.db.session import AsyncSessionLocal
from app.db.user import User
from sqlalchemy import select

class SentryContext(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if data.get("sentry_enabled", False):
            async with AsyncSessionLocal() as s:
                user = await s.scalar(select(User).where(User.tg_id == event.from_user.id))
            await enrich_scope(event, user or User(login="unknown", role="guest"))
        return await handler(event, data) 