from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Broadcast(Base):
    """Модель массовых рассылок"""

    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    target_role = Column(String(50), nullable=False)  # "teacher", "student", etc.
    status = Column(String(50), default="sent")  # "draft", "sent", "delivered"
    sent_at = Column(DateTime, server_default=func.now())

    # Связи
    author = relationship("User", back_populates="broadcasts")

    def __repr__(self) -> str:
        return f"<Broadcast(id={self.id}, title='{self.title}', status={self.status})>"
