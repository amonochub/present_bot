from sqlalchemy import select, update

from app.db.enums import Status
from app.db.psych_request import PsychRequest
from app.db.session import AsyncSessionLocal


async def create(from_id: int, text: str | None, file_id: str | None) -> None:
    async with AsyncSessionLocal() as s:
        s.add(PsychRequest(from_id=from_id, text=text, content_id=file_id))
        await s.commit()


async def list_open() -> list[PsychRequest]:
    async with AsyncSessionLocal() as s:
        rows = await s.scalars(
            select(PsychRequest)
            .where(PsychRequest.status == Status.open)
            .order_by(PsychRequest.created_at)
        )
        return list(rows)


async def mark_done(req_id: int) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(PsychRequest).where(PsychRequest.id == req_id).values(status=Status.done)
        )
        await s.commit()
