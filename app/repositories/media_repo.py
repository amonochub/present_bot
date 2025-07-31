from datetime import date
from typing import List

from sqlalchemy import select, update

from app.db.enums import Status
from app.db.media_request import MediaRequest
from app.db.session import AsyncSessionLocal


async def create(author_id: int, event_date: date, comment: str, file_id: str) -> None:
    async with AsyncSessionLocal() as s:
        s.add(
            MediaRequest(
                author_id=author_id,
                event_date=event_date,
                comment=comment,
                file_id=file_id,
            )
        )
        await s.commit()


async def list_all() -> List[MediaRequest]:
    async with AsyncSessionLocal() as s:
        rows = await s.scalars(
            select(MediaRequest).order_by(MediaRequest.created_at.desc())
        )
        return list(rows)


async def set_status(req_id: int, status: Status) -> bool:
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(
                update(MediaRequest)
                .where(MediaRequest.id == req_id)
                .values(status=status)
            )
            await s.commit()
            return True
    except Exception:
        return False
