from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime, Date
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, date

from app.db.base import Base, TimestampMixin


class TaskStatus(enum.Enum):
    """Статусы поручений"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    """Приоритеты поручений"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, TimestampMixin):
    """Модель поручений"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date = Column(DateTime, nullable=True)
    deadline = Column(Date, nullable=True)  # Дедлайн для KPI
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связи
    author = relationship("User", foreign_keys=[author_id], back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>" 