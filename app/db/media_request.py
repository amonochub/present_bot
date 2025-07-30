from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey, Enum
from app.db.base import Base
from app.db.enums import Status

class MediaRequest(Base):
    __tablename__ = "media_requests"
    id          = Column(Integer, primary_key=True)
    author_id   = Column(Integer, ForeignKey("users.id"))
    event_date  = Column(Date)          # дата мероприятия
    comment     = Column(String)        # краткое описание/сценарий
    file_id     = Column(String)        # обязательный Telegram file_id
    status      = Column(Enum(Status), default=Status.open, nullable=False)  # open / in_progress / done
    created_at  = Column(DateTime, server_default=func.now()) 