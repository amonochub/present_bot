from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.repositories.user_repo import get_user
from app.services.feedback_service import feedback_service
from app.services.onboarding_service import onboarding_service

router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start с онбордингом"""
    user = await get_user(message.from_user.id)

    if not user or not user.seen_intro:
        # Показываем онбординг для новых пользователей
        await onboarding_service.start_onboarding(message, state)
    else:
        # Показываем приветствие в зависимости от роли
        from app.i18n import t

        role_messages = {
            "student": t("start.student"),
            "parent": t("start.parent"),
            "teacher": t("start.teacher"),
            "admin": t("start.admin"),
            "director": t("start.admin"),  # Директор использует то же сообщение
            "psych": t("start.teacher"),  # Психолог использует сообщение учителя
        }

        welcome_message = role_messages.get(user.role, t("start.unknown"))

        # Показываем обычное меню для существующих пользователей
        from app.keyboards.main_menu import menu

        await message.answer(welcome_message, reply_markup=menu(user.role, "ru"))


@router.callback_query(F.data.startswith("onboarding:role:"))
async def handle_role_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора роли в онбординге"""
    await onboarding_service.handle_role_selection(callback, state)


@router.callback_query(F.data == "onboarding:confirm_role")
async def confirm_role_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик подтверждения выбора роли"""
    await onboarding_service.confirm_role(callback, state)


@router.callback_query(F.data == "onboarding:change_role")
async def change_role_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик изменения выбора роли"""
    await onboarding_service.change_role(callback, state)


@router.message(Command("feedback"))
async def feedback_command(message: Message, state: FSMContext) -> None:
    """Обработчик команды /feedback"""
    await feedback_service.start_feedback(message, state)


@router.callback_query(F.data.startswith("feedback:type:"))
async def handle_feedback_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора типа обратной связи"""
    await feedback_service.handle_feedback_type(callback, state)


@router.callback_query(F.data == "feedback:cancel")
async def cancel_feedback(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены обратной связи"""
    await feedback_service.cancel_feedback(callback, state)


@router.message(F.text)
async def handle_feedback_text(message: Message, state: FSMContext) -> None:
    """Обработчик текста обратной связи"""
    current_state = await state.get_state()

    if current_state == "feedback:text_input":
        await feedback_service.handle_feedback_text(message, state)
