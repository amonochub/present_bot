from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Enum
from app.db.base import Base
from app.db.enums import Status

class Ticket(Base):
    __tablename__ = "tickets"
    id          = Column(Integer, primary_key=True)
    author_id   = Column(Integer, ForeignKey("users.id"))
    title       = Column(String)          # краткое описание
    file_id     = Column(String, nullable=True)  # фото/док
    status      = Column(Enum(Status), default=Status.open, nullable=False) # open / in_progress / done
    created_at  = Column(DateTime, server_default=func.now()) 