"""
Сервис для управления командами Telegram бота
"""

from typing import List, Optional

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeChatAdministrators,
    BotCommandScopeDefault,
)

from app.i18n import t
from app.roles import UserRole


class CommandService:
    """Сервис для управления командами бота"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def setup_commands(self) -> None:
        """Устанавливает команды по умолчанию для всех пользователей"""
        commands = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="help", description="❓ Справка"),
            BotCommand(command="menu", description="🏠 Главное меню"),
            BotCommand(command="feedback", description="💬 Обратная связь"),
            BotCommand(command="theme", description="🌗 Сменить тему"),
        ]

        await self.bot.set_my_commands(
            commands, scope=BotCommandScopeDefault()
        )

    async def setup_role_commands(
        self, user_id: int, role: UserRole, lang: str = "ru"
    ) -> None:
        """Устанавливает команды для конкретной роли пользователя"""

        # Базовые команды для всех ролей
        base_commands = [
            BotCommand(command="start", description=t("commands.start", lang)),
            BotCommand(command="help", description=t("commands.help", lang)),
            BotCommand(command="menu", description=t("commands.menu", lang)),
            BotCommand(
                command="feedback", description=t("commands.feedback", lang)
            ),
            BotCommand(command="theme", description=t("commands.theme", lang)),
        ]

        # Ролевые команды
        role_commands = self._get_role_commands(role, lang)

        # Объединяем команды
        all_commands = base_commands + role_commands

        # Устанавливаем команды для пользователя
        scope = BotCommandScopeChat(chat_id=user_id)
        await self.bot.set_my_commands(all_commands, scope=scope)

    def _get_role_commands(
        self, role: UserRole, lang: str
    ) -> List[BotCommand]:
        """Возвращает команды для конкретной роли"""

        commands_map = {
            UserRole.STUDENT: [
                BotCommand(
                    command="tasks",
                    description=t("commands.student.tasks", lang),
                ),
                BotCommand(
                    command="notes",
                    description=t("commands.student.notes", lang),
                ),
                BotCommand(
                    command="ask", description=t("commands.student.ask", lang)
                ),
                BotCommand(
                    command="ticket",
                    description=t("commands.student.ticket", lang),
                ),
            ],
            UserRole.TEACHER: [
                BotCommand(
                    command="notes",
                    description=t("commands.teacher.notes", lang),
                ),
                BotCommand(
                    command="addnote",
                    description=t("commands.teacher.addnote", lang),
                ),
                BotCommand(
                    command="ticket",
                    description=t("commands.teacher.ticket", lang),
                ),
                BotCommand(
                    command="students",
                    description=t("commands.teacher.students", lang),
                ),
            ],
            UserRole.PARENT: [
                BotCommand(
                    command="tasks",
                    description=t("commands.parent.tasks", lang),
                ),
                BotCommand(
                    command="cert", description=t("commands.parent.cert", lang)
                ),
                BotCommand(
                    command="progress",
                    description=t("commands.parent.progress", lang),
                ),
                BotCommand(
                    command="ticket",
                    description=t("commands.parent.ticket", lang),
                ),
            ],
            UserRole.PSYCHOLOGIST: [
                BotCommand(
                    command="inbox",
                    description=t("commands.psych.inbox", lang),
                ),
                BotCommand(
                    command="requests",
                    description=t("commands.psych.requests", lang),
                ),
                BotCommand(
                    command="schedule",
                    description=t("commands.psych.schedule", lang),
                ),
            ],
            UserRole.ADMIN: [
                BotCommand(
                    command="tickets",
                    description=t("commands.admin.tickets", lang),
                ),
                BotCommand(
                    command="broadcast",
                    description=t("commands.admin.broadcast", lang),
                ),
                BotCommand(
                    command="users",
                    description=t("commands.admin.users", lang),
                ),
                BotCommand(
                    command="stats",
                    description=t("commands.admin.stats", lang),
                ),
            ],
            UserRole.DIRECTOR: [
                BotCommand(
                    command="kpi", description=t("commands.director.kpi", lang)
                ),
                BotCommand(
                    command="stats",
                    description=t("commands.director.stats", lang),
                ),
                BotCommand(
                    command="reports",
                    description=t("commands.director.reports", lang),
                ),
                BotCommand(
                    command="tasks",
                    description=t("commands.director.tasks", lang),
                ),
            ],
        }

        return commands_map.get(role, [])

    async def clear_user_commands(self, user_id: int) -> None:
        """Очищает команды для пользователя"""
        scope = BotCommandScopeChat(chat_id=user_id)
        await self.bot.delete_my_commands(scope=scope)

    async def setup_admin_commands(self) -> None:
        """Устанавливает команды для администраторов"""
        admin_commands = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="help", description="❓ Справка"),
            BotCommand(command="admin", description="⚙️ Панель администратора"),
            BotCommand(command="stats", description="📊 Статистика"),
            BotCommand(command="broadcast", description="📢 Рассылка"),
            BotCommand(command="users", description="👥 Пользователи"),
            BotCommand(command="tickets", description="🛠 Заявки"),
        ]

        await self.bot.set_my_commands(
            admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=0)
        )


# Глобальный экземпляр сервиса
command_service: Optional[CommandService] = None


def init_command_service(bot: Bot) -> None:
    """Инициализирует глобальный сервис команд"""
    global command_service
    command_service = CommandService(bot)


async def setup_all_commands() -> None:
    """Устанавливает все команды при запуске бота"""
    if command_service:
        await command_service.setup_commands()
        await command_service.setup_admin_commands()
