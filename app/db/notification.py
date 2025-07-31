import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class NotificationType(enum.Enum):
    """Типы уведомлений"""

    TASK_REMINDER = "task_reminder"
    TASK_DEADLINE = "task_deadline"
    BROADCAST = "broadcast"
    NOTE_CREATED = "note_created"
    TICKET_UPDATED = "ticket_updated"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"


class NotificationStatus(enum.Enum):
    """Статусы уведомлений"""

    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


class Notification(Base, TimestampMixin):
    """Модель уведомлений"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: NotificationType = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status: NotificationStatus = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)  # Когда отправить
    sent_at = Column(DateTime, nullable=True)  # Когда было отправлено
    read_at = Column(DateTime, nullable=True)  # Когда было прочитано

    # Дополнительные данные (JSON)
    metadata: str = Column(String, nullable=True)  # Дополнительные данные

    # Связи
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"
