from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from sqlalchemy.ext.declarative import DeclarativeBase

Base: "DeclarativeBase" = declarative_base()


class TimestampMixin:
    """Миксин для добавления временных меток"""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Импортируем все модели для создания таблиц
from .user import User  # noqa
from .note import Note  # noqa
from .ticket import Ticket  # noqa
from .task import Task  # noqa
from .psych_request import PsychRequest  # noqa
from .media_request import MediaRequest  # noqa
from .broadcast import Broadcast  # noqa
from .notification import Notification  # noqa
