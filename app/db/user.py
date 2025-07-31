from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .broadcast import Broadcast
    from .note import Note
    from .notification import Notification
    from .task import Task


class User(Base, TimestampMixin):
    """Модель пользователя"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True, nullable=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, nullable=False)  # Простые строковые роли
    is_active = Column(Boolean, default=True, nullable=False)

    # Демо-логин поля
    login = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    used = Column(Boolean, default=False, nullable=False)

    # UX настройки
    theme = Column(String, default="light")  # 'light' | 'dark'
    seen_intro = Column(Boolean, default=False, nullable=False)  # Прошел ли онбординг

    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    email_notifications = Column(Boolean, default=False, nullable=False)

    # Связи
    notes = relationship("Note", back_populates="teacher")
    tasks = relationship(
        "Task", foreign_keys="Task.author_id", back_populates="author"
    )
    broadcasts = relationship("Broadcast", back_populates="author")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, tg_id={self.tg_id}, role={self.role})>"
