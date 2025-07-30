from pydantic import BaseModel, Field
from datetime import datetime

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    file_id: str | None = None

class TicketRead(TicketCreate):
    id: int
    status: str
    created_at: datetime 