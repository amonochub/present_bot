from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """Модель заметок"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_name = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    
    # Связи
    teacher = relationship("User", back_populates="notes")
    
    def __repr__(self):
        return f"<Note(id={self.id}, student_name='{self.student_name}', teacher_id={self.teacher_id})>" 