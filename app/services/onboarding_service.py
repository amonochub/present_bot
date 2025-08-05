"""
Сервис для онбординга новых пользователей
"""

import asyncio

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.i18n import t
from app.repositories.user_repo import create_user, get_user, update_user_intro
from app.roles import UserRole
from app.services.command_service import command_service


class OnboardingService:
    """Сервис для онбординга новых пользователей"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def start_onboarding(
        self, message: Message, state: FSMContext
    ) -> None:
        """Начинает процесс онбординга для нового пользователя"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(message.chat.id, "typing")

        # Небольшая задержка для лучшего UX
        await asyncio.sleep(0.5)

        # Проверяем, существует ли пользователь
        user = await get_user(message.from_user.id)

        if not user:
            # Создаём нового пользователя
            user = await create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                role=UserRole.STUDENT,  # Роль по умолчанию
            )

        # Показываем приветственное сообщение
        welcome_text = t("onboarding.welcome", "ru")
        keyboard = self._get_role_selection_keyboard()

        await message.answer(
            welcome_text, reply_markup=keyboard, parse_mode="HTML"
        )

        # Устанавливаем состояние онбординга
        await state.set_state("onboarding:role_selection")

    async def handle_role_selection(
        self, callback: CallbackQuery, state: FSMContext
    ) -> None:
        """Обрабатывает выбор роли пользователем"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(callback.message.chat.id, "typing")

        role_data = callback.data.split(":")[1]
        role = UserRole(role_data)

        # Обновляем роль пользователя
        user = await get_user(callback.from_user.id)
        if user:
            user.role = role
            await user.save()

            # Устанавливаем команды для новой роли
            if command_service:
                await command_service.setup_role_commands(
                    callback.from_user.id, role, "ru"
                )

        # Показываем подтверждение выбора роли
        confirmation_text = t("onboarding.role_confirmation", "ru")
        role_name = t(f"roles.{role.value}", "ru")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data="onboarding:confirm_role",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Выбрать другую",
                        callback_data="onboarding:change_role",
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            f"{confirmation_text}\n\n🎯 Выбранная роль: <b>{role_name}</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        await callback.answer()

    async def confirm_role(
        self, callback: CallbackQuery, state: FSMContext
    ) -> None:
        """Подтверждает выбор роли и завершает онбординг"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(callback.message.chat.id, "typing")

        # Обновляем статус онбординга
        await update_user_intro(callback.from_user.id, True)

        # Очищаем состояние
        await state.clear()

        # Показываем финальное сообщение
        user = await get_user(callback.from_user.id)
        role_name = t(f"roles.{user.role.value}", "ru")

        final_text = f"""
🎉 Отлично! Онбординг завершён.

✅ Ваша роль: <b>{role_name}</b>
📱 Теперь вам доступны команды в меню бота
❓ Используйте /help для получения справки
🏠 /menu - для доступа к главному меню

Добро пожаловать в SchoolBot! 🎓
        """.strip()

        from app.keyboards.main_menu import menu

        keyboard = menu(user.role, "ru")

        await callback.message.edit_text(
            final_text, reply_markup=keyboard, parse_mode="HTML"
        )

        await callback.answer()

    async def change_role(
        self, callback: CallbackQuery, state: FSMContext
    ) -> None:
        """Возвращает к выбору роли"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(callback.message.chat.id, "typing")

        welcome_text = t("onboarding.welcome", "ru")
        keyboard = self._get_role_selection_keyboard()

        await callback.message.edit_text(
            welcome_text, reply_markup=keyboard, parse_mode="HTML"
        )

        await callback.answer()

    def _get_role_selection_keyboard(self) -> InlineKeyboardMarkup:
        """Создаёт клавиатуру для выбора роли"""

        roles = [
            ("👨‍🎓 Ученик", "onboarding:role:student"),
            ("👩‍🏫 Учитель", "onboarding:role:teacher"),
            ("👪 Родитель", "onboarding:role:parent"),
            ("🧑‍⚕️ Психолог", "onboarding:role:psychologist"),
            ("🏛 Администратор", "onboarding:role:admin"),
            ("📈 Директор", "onboarding:role:director"),
        ]

        keyboard = []
        for role_name, callback_data in roles:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=role_name, callback_data=callback_data
                    )
                ]
            )

        return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Глобальный экземпляр сервиса
onboarding_service: OnboardingService = None


def init_onboarding_service(bot: Bot) -> None:
    """Инициализирует глобальный сервис онбординга"""
    global onboarding_service
    onboarding_service = OnboardingService(bot)
