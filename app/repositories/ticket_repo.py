from typing import List

from sqlalchemy import select, update

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.ticket import Ticket
from app.middlewares.metrics import decrement_tickets, increment_tickets


async def create_ticket(
    author_id: int, title: str, file_id: str | None
) -> Ticket:
    async with AsyncSessionLocal() as s:
        ticket = Ticket(author_id=author_id, title=title, file_id=file_id)
        s.add(ticket)
        await s.commit()
        await s.refresh(ticket)
        # Увеличиваем счетчик открытых заявок
        increment_tickets()
        return ticket


async def list_all() -> List[Ticket]:
    async with AsyncSessionLocal() as s:
        rows = await s.scalars(
            select(Ticket).order_by(Ticket.created_at.desc())
        )
        return list(rows)


async def set_status(tkt_id: int, status: Status) -> bool:
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(
                update(Ticket).where(Ticket.id == tkt_id).values(status=status)
            )
            await s.commit()
            # Если заявка закрыта, уменьшаем счетчик
            if status == Status.done:
                decrement_tickets()
            return True
    except Exception:
        return False
