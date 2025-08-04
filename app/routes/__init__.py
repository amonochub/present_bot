from typing import Any

from .admin import router as admin
from .director import router as director
from .docs import router as docs
from .help import router as help_router
from .intro import router as intro
from .onboarding import router as onboarding
from .parent import router as parent
from .psych import router as psych
from .student import router as student
from .teacher import router as teacher
from .theme import router as theme
from .tour import router as tour


def include_all(dp: Any) -> None:
    """Include all routers in the dispatcher"""
    dp.include_router(intro)  # Подключаем первым для обработки /start
    dp.include_router(onboarding)  # Подключаем онбординг
    dp.include_router(docs)  # Подключаем документы и новости
    dp.include_router(teacher)
    dp.include_router(admin)
    dp.include_router(director)
    dp.include_router(parent)
    dp.include_router(student)
    dp.include_router(psych)
    dp.include_router(help_router)
    dp.include_router(theme)
    dp.include_router(tour)


__all__ = [
    "intro",
    "onboarding",
    "docs",
    "teacher",
    "admin",
    "director",
    "parent",
    "student",
    "psych",
    "help_router",
    "theme",
    "tour",
    "include_all",
]
