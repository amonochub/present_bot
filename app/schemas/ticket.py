from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    file_id: str | None = None


class TicketRead(TicketCreate):
    id: int
    status: str
    created_at: datetime
