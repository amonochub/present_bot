# app/handlers/onboarding.py
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.keyboards.onboarding import get_role_selection_keyboard
from app.roles import ROLES

router = Router()


class OnboardingStates(StatesGroup):
    """Состояния для процесса онбординга"""

    selecting_role = State()
    confirming_role = State()


# Словарь соответствия ролей и изображений
ROLE_IMAGES = {
    "teacher": "onboard_cards_v3/onboard_teacher.png",
    "admin": "onboard_cards_v3/onboard_admin.png",
    "director": "onboard_cards_v3/onboard_director.png",
    "parent": "onboard_cards_v3/onboard_parent.png",
    "student": "onboard_cards_v3/onboard_student.png",
    "psych": "onboard_cards_v3/onboard_psych.png",
}

# Описания ролей для онбординга
ROLE_DESCRIPTIONS = {
    "teacher": {
        "title": "👩‍🏫 Учитель",
        "description": "• Создание и управление заметками\n• Подача заявок в техподдержку\n• Доступ к медиа-материалам\n• Взаимодействие с учениками и родителями",
    },
    "admin": {
        "title": "🏛 Администрация",
        "description": "• Управление заявками пользователей\n• Создание рассылок\n• Доступ к медиа-материалам\n• Администрирование системы",
    },
    "director": {
        "title": "📈 Директор",
        "description": "• Просмотр статистики и KPI\n• Управление пользователями\n• Мониторинг активности\n• Аналитика по всем процессам",
    },
    "parent": {
        "title": "👪 Родитель",
        "description": "• Просмотр заданий детей\n• Получение справок\n• Создание заметок\n• Связь с учителями",
    },
    "student": {
        "title": "👨‍🎓 Ученик",
        "description": "• Просмотр заданий\n• Создание заметок\n• Задавание вопросов\n• Подача заявок в техподдержку",
    },
    "psych": {
        "title": "🧑‍⚕️ Психолог",
        "description": "• Просмотр запросов на консультацию\n• Управление обращениями\n• Поддержка учеников и родителей\n• Профессиональная помощь",
    },
}


@router.message(Command("onboard"))
async def start_onboarding(message: Message, state: FSMContext, lang: str) -> None:
    """Начало процесса онбординга"""
    await state.set_state(OnboardingStates.selecting_role)

    welcome_text = (
        "🎓 **Добро пожаловать в SchoolBot!**\n\n"
        "Выберите вашу роль в образовательном процессе:\n\n"
        "Каждая роль предоставляет уникальные возможности для эффективной работы в школе."
    )

    await message.answer(
        welcome_text, reply_markup=get_role_selection_keyboard(), parse_mode="Markdown"
    )


@router.message(Command("carousel"))
async def show_role_carousel(message: Message, state: FSMContext, lang: str) -> None:
    """Показать карусель всех ролей"""
    await state.set_state(OnboardingStates.selecting_role)

    # Отправляем первое изображение с каруселью
    await send_role_carousel(message, 0, lang)


async def send_role_carousel(message: Message, current_index: int, lang: str) -> None:
    """Отправить карусель ролей"""
    roles = list(ROLES.keys())
    if current_index >= len(roles):
        current_index = 0

    role = roles[current_index]
    role_info = ROLE_DESCRIPTIONS[role]

    try:
        image_path = ROLE_IMAGES[role]
        photo = FSInputFile(image_path)

        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            f"📄 {current_index + 1} из {len(roles)}"
        )

        # Создаем клавиатуру для карусели
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard_buttons = []

        # Кнопки навигации
        nav_row = []
        if len(roles) > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"carousel_{(current_index - 1) % len(roles)}",
                )
            )
            nav_row.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"carousel_{(current_index + 1) % len(roles)}",
                )
            )
        keyboard_buttons.append(nav_row)

        # Кнопка выбора роли
        keyboard_buttons.append(
            [InlineKeyboardButton(text=f"✅ Выбрать {ROLES[role]}", callback_data=f"role_{role}")]
        )

        # Кнопка выхода из карусели
        keyboard_buttons.append(
            [InlineKeyboardButton(text="🔙 К списку ролей", callback_data="back_to_roles")]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer_photo(
            photo=photo, caption=caption, reply_markup=keyboard, parse_mode="Markdown"
        )

    except Exception:
        # Если изображение не найдено, отправляем только текст
        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            f"📄 {current_index + 1} из {len(roles)}"
        )

        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard_buttons = []

        # Кнопки навигации
        nav_row = []
        if len(roles) > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"carousel_{(current_index - 1) % len(roles)}",
                )
            )
            nav_row.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"carousel_{(current_index + 1) % len(roles)}",
                )
            )
        keyboard_buttons.append(nav_row)

        # Кнопка выбора роли
        keyboard_buttons.append(
            [InlineKeyboardButton(text=f"✅ Выбрать {ROLES[role]}", callback_data=f"role_{role}")]
        )

        # Кнопка выхода из карусели
        keyboard_buttons.append(
            [InlineKeyboardButton(text="🔙 К списку ролей", callback_data="back_to_roles")]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(caption, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith("role_"))
async def handle_role_selection(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Обработка выбора роли"""
    role = callback.data.split("_", 1)[1]

    if role not in ROLES:
        await callback.answer("Неизвестная роль", show_alert=True)
        return

    # Сохраняем выбранную роль
    await state.update_data(selected_role=role)
    await state.set_state(OnboardingStates.confirming_role)

    # Получаем описание роли
    role_info = ROLE_DESCRIPTIONS[role]

    # Отправляем изображение с описанием
    try:
        image_path = ROLE_IMAGES[role]
        photo = FSInputFile(image_path)

        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            "✅ **Подтвердите выбор роли**"
        )

        if callback.message is not None:
            await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")

            # Обновляем клавиатуру для подтверждения
            from app.keyboards.onboarding import get_confirmation_keyboard

            await callback.message.edit_reply_markup(reply_markup=get_confirmation_keyboard(role))

    except Exception:
        # Если изображение не найдено, отправляем только текст
        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            "✅ **Подтвердите выбор роли**"
        )

        if callback.message is not None:
            await callback.message.answer(caption, parse_mode="Markdown")

            from app.keyboards.onboarding import get_confirmation_keyboard

            await callback.message.edit_reply_markup(reply_markup=get_confirmation_keyboard(role))

    await callback.answer()


@router.callback_query(F.data.startswith("confirm_role_"))
async def handle_role_confirmation(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Подтверждение выбора роли"""
    role = callback.data.split("_", 2)[2]

    if role not in ROLES:
        await callback.answer("Неизвестная роль", show_alert=True)
        return

    # Получаем данные пользователя
    data = await state.get_data()
    selected_role = data.get("selected_role")

    if selected_role != role:
        await callback.answer("Ошибка: роль не совпадает", show_alert=True)
        return

    # Здесь можно добавить логику создания пользователя
    # или перехода к авторизации

    success_text = (
        f"🎉 **Отлично!**\n\n"
        f"Вы выбрали роль: **{ROLES[role]}**\n\n"
        "Теперь вы можете:\n"
        "• Использовать команду /start для входа\n"
        "• Ознакомиться с функциями через /help\n"
        "• Пройти тур по возможностям через /tour"
    )

    if callback.message is not None:
        await callback.message.answer(success_text, parse_mode="Markdown")

    # Очищаем состояние
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "back_to_roles")
async def back_to_role_selection(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Возврат к выбору роли"""
    await state.set_state(OnboardingStates.selecting_role)

    if callback.message is not None:
        await callback.message.edit_text(
            "🎓 **Выберите вашу роль:**\n\n"
            "Каждая роль предоставляет уникальные возможности для эффективной работы в школе.",
            reply_markup=get_role_selection_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(F.data == "start_carousel")
async def handle_start_carousel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Запуск карусели ролей"""
    if callback.message is not None:
        await send_role_carousel(callback.message, 0, lang)
    await callback.answer()


@router.callback_query(F.data.startswith("carousel_"))
async def handle_carousel_navigation(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Обработка навигации по карусели"""
    try:
        index = int(callback.data.split("_", 1)[1])
        if callback.message is not None:
            await send_role_carousel(callback.message, index, lang)
        await callback.answer()
    except (ValueError, IndexError):
        await callback.answer("Ошибка навигации", show_alert=True)


@router.callback_query(F.data.startswith("info_"))
async def show_role_info(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Показать информацию о роли"""
    role = callback.data.split("_", 1)[1]

    if role not in ROLES:
        await callback.answer("Неизвестная роль", show_alert=True)
        return

    role_info = ROLE_DESCRIPTIONS[role]

    try:
        image_path = ROLE_IMAGES[role]
        photo = FSInputFile(image_path)

        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            "💡 **Нажмите кнопку ниже, чтобы выбрать эту роль**"
        )

        if callback.message is not None:
            await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")

            # Кнопка для выбора этой роли
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"✅ Выбрать роль: {ROLES[role]}",
                            callback_data=f"role_{role}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад к списку ролей",
                            callback_data="back_to_roles",
                        )
                    ],
                ]
            )

            await callback.message.edit_reply_markup(reply_markup=keyboard)

    except Exception:
        # Если изображение не найдено, отправляем только текст
        caption = (
            f"**{role_info['title']}**\n\n"
            f"{role_info['description']}\n\n"
            "💡 **Нажмите кнопку ниже, чтобы выбрать эту роль**"
        )

        if callback.message is not None:
            await callback.message.answer(caption, parse_mode="Markdown")

            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"✅ Выбрать роль: {ROLES[role]}",
                            callback_data=f"role_{role}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад к списку ролей",
                            callback_data="back_to_roles",
                        )
                    ],
                ]
            )

            await callback.message.edit_reply_markup(reply_markup=keyboard)

    await callback.answer()
