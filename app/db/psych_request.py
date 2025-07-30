from sqlalchemy import Column, DateTime, Enum, Integer, String, func

from app.db.base import Base
from app.db.enums import Status


class PsychRequest(Base):
    __tablename__ = "psych_requests"
    id = Column(Integer, primary_key=True)
    from_id = Column(Integer)  # Telegram-ID автора (анонимный, хранится лишь ID)
    content_id = Column(String, nullable=True)  # file_id голосового / None если текст
    text = Column(String, nullable=True)  # текст обращения (если не voice)
    status = Column(Enum(Status), default=Status.open, nullable=False)  # open / done
    created_at = Column(DateTime, server_default=func.now())
