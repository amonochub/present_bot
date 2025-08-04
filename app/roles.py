# app/roles.py
from enum import Enum

from app.utils.hash import hash_pwd


class UserRole(Enum):
    """Роли пользователей в системе"""

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    PSYCHOLOGIST = "psych"
    ADMIN = "admin"
    DIRECTOR = "director"
    SUPER = "super"  # Демо-режим


# Алиас для обратной совместимости
Role = UserRole

ROLES = {
    "teacher": "Учитель",
    "admin": "Администрация",
    "director": "Директор",
    "student": "Ученик",
    "parent": "Родитель",
    "psych": "Психолог",
    "super": "Демо-режим",  # «универсальная» роль
}


def _make(prefix: str, n: int, pwd: str, role: str) -> list[dict[str, str]]:
    return [
        {
            "login": f"{prefix}{str(i).zfill(2)}",
            "password": hash_pwd(pwd),
            "role": role,
            "theme": "light",
        }  # дефолтная тема
        for i in range(1, n + 1)
    ]


DEMO_USERS = (
    _make("teacher", 5, "teacher", "teacher")
    + _make("admin", 5, "admin", "admin")
    + _make("director", 5, "director", "director")
    + _make("student", 10, "student", "student")
    + _make("parent", 10, "parent", "parent")
    + _make("psy", 5, "psy", "psych")
    + [{"login": "demo01", "password": hash_pwd("demo"), "role": "super", "theme": "light"}]  # ← FIXED
)
