from typing import Any

from sentry_sdk import push_scope


async def enrich_scope(update: Any, user: Any) -> None:
    """
    Добавить в текущий Sentry-scope:
    • role (teacher / admin / …)
    • chat_id
    • callback_data (если есть)
    """
    with push_scope() as scope:
        scope.set_tag("role", user.role)
        scope.set_tag("chat_id", update.chat.id if hasattr(update, "chat") else "n/a")
        if hasattr(update, "data"):
            scope.set_extra("callback_data", update.data[:100])
