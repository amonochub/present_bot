import enum


class Status(str, enum.Enum):
    """Глобальный enum для статусов"""

    open = "open"
    in_progress = "in_progress"
    done = "done"


def ico(status: Status) -> str:
    """Возвращает иконку для статуса"""
    return {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}[
        status
    ]
