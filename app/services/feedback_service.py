"""
Сервис для обработки обратной связи от пользователей
"""

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import settings
from app.repositories.ticket_repo import create_ticket
from app.repositories.user_repo import get_user


class FeedbackService:
    """Сервис для обработки обратной связи"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def start_feedback(
        self, message: Message, state: FSMContext
    ) -> None:
        """Начинает процесс отправки обратной связи"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(message.chat.id, "typing")

        # Получаем пользователя
        user = await get_user(message.from_user.id)

        feedback_text = """
💬 Обратная связь

Здесь вы можете:
• 📝 Оставить отзыв о работе бота
• 🐛 Сообщить об ошибке
• 💡 Предложить улучшения
• ❓ Задать вопрос

Выберите тип обращения:
        """.strip()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Отзыв", callback_data="feedback:type:review"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🐛 Ошибка", callback_data="feedback:type:bug"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💡 Предложение",
                        callback_data="feedback:type:suggestion",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❓ Вопрос",
                        callback_data="feedback:type:question",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="feedback:cancel"
                    )
                ],
            ]
        )

        await message.answer(
            feedback_text, reply_markup=keyboard, parse_mode="HTML"
        )

        await state.set_state("feedback:type_selection")

    async def handle_feedback_type(
        self, callback: CallbackQuery, state: FSMContext
    ) -> None:
        """Обрабатывает выбор типа обратной связи"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(callback.message.chat.id, "typing")

        feedback_type = callback.data.split(":")[2]

        # Сохраняем тип обратной связи
        await state.update_data(feedback_type=feedback_type)

        # Показываем инструкцию для ввода текста
        type_messages = {
            "review": "📝 Поделитесь своими впечатлениями о работе бота. Что вам понравилось, а что можно улучшить?",
            "bug": "🐛 Опишите проблему, которую вы обнаружили. Укажите, что вы делали, когда произошла ошибка.",
            "suggestion": "💡 Расскажите о вашей идее улучшения. Как это поможет пользователям?",
            "question": "❓ Задайте ваш вопрос. Мы постараемся ответить как можно скорее.",
        }

        instruction = type_messages.get(feedback_type, "Введите ваш текст:")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Отмена", callback_data="feedback:cancel"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            f"{instruction}\n\n✍️ Введите ваш текст:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        await state.set_state("feedback:text_input")
        await callback.answer()

    async def handle_feedback_text(
        self, message: Message, state: FSMContext
    ) -> None:
        """Обрабатывает текст обратной связи"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(message.chat.id, "typing")

        # Получаем данные из состояния
        data = await state.get_data()
        feedback_type = data.get("feedback_type", "general")

        # Проверяем длину текста
        if len(message.text) > 1000:
            await message.answer(
                "⚠️ Текст слишком длинный (максимум 1000 символов). Сократите сообщение.",
                parse_mode="HTML",
            )
            return

        # Создаём тикет обратной связи
        user = await get_user(message.from_user.id)

        ticket_data = {
            "title": f"Обратная связь: {feedback_type}",
            "description": message.text,
            "author_id": user.id,
            "status": "open",
            "type": "feedback",
            "priority": "normal",
        }

        ticket = await create_ticket(**ticket_data)

        # Показываем подтверждение
        confirmation_text = f"""
✅ Спасибо за обратную связь!

📝 Ваше сообщение принято и будет рассмотрено.
🆔 Номер обращения: #{ticket.id}
⏰ Мы ответим вам в ближайшее время.

Если у вас есть дополнительные вопросы, используйте команду /feedback
        """.strip()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏠 Главное меню", callback_data="menu:main"
                    )
                ]
            ]
        )

        await message.answer(
            confirmation_text, reply_markup=keyboard, parse_mode="HTML"
        )

        # Очищаем состояние
        await state.clear()

        # Отправляем уведомление администраторам
        await self._notify_admins(ticket, user)

    async def cancel_feedback(
        self, callback: CallbackQuery, state: FSMContext
    ) -> None:
        """Отменяет процесс отправки обратной связи"""

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(callback.message.chat.id, "typing")

        # Очищаем состояние
        await state.clear()

        # Показываем сообщение об отмене
        await callback.message.edit_text(
            "❌ Отправка обратной связи отменена.\n\nЕсли у вас есть вопросы, используйте команду /feedback",
            parse_mode="HTML",
        )

        await callback.answer()

    async def _notify_admins(self, ticket, user) -> None:
        """Отправляет уведомление администраторам о новой обратной связи"""

        if not settings.ADMIN_IDS:
            return

        admin_ids = [
            int(admin_id.strip()) for admin_id in settings.ADMIN_IDS.split(",")
        ]

        notification_text = f"""
📬 Новая обратная связь

👤 От: {user.first_name} {user.last_name or ''}
🆔 ID: {user.telegram_id}
📝 Тип: {ticket.title}
📄 Текст: {ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}
🆔 Тикет: #{ticket.id}
        """.strip()

        for admin_id in admin_ids:
            try:
                await self.bot.send_message(
                    admin_id, notification_text, parse_mode="HTML"
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                print(f"Ошибка отправки уведомления админу {admin_id}: {e}")


# Глобальный экземпляр сервиса
feedback_service: FeedbackService = None


def init_feedback_service(bot: Bot) -> None:
    """Инициализирует глобальный сервис обратной связи"""
    global feedback_service
    feedback_service = FeedbackService(bot)
