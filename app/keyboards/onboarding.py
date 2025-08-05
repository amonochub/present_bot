# app/keyboards/onboarding.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора роли"""
    keyboard = []

    # Первый ряд: Учитель и Администрация
    row1 = [
        InlineKeyboardButton(
            text="👩‍🏫 Учитель", callback_data="role_teacher"
        ),
        InlineKeyboardButton(
            text="🏛 Администрация", callback_data="role_admin"
        ),
    ]
    keyboard.append(row1)

    # Второй ряд: Директор и Родитель
    row2 = [
        InlineKeyboardButton(
            text="📈 Директор", callback_data="role_director"
        ),
        InlineKeyboardButton(text="👪 Родитель", callback_data="role_parent"),
    ]
    keyboard.append(row2)

    # Третий ряд: Ученик и Психолог
    row3 = [
        InlineKeyboardButton(text="👨‍🎓 Ученик", callback_data="role_student"),
        InlineKeyboardButton(text="🧑‍⚕️ Психолог", callback_data="role_psych"),
    ]
    keyboard.append(row3)

    # Четвертый ряд: Карусель всех ролей
    row4 = [
        InlineKeyboardButton(
            text="🖼 Просмотреть все роли", callback_data="start_carousel"
        )
    ]
    keyboard.append(row4)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(role: str) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения выбора роли"""
    keyboard = []

    # Кнопка подтверждения
    confirm_button = InlineKeyboardButton(
        text="✅ Подтвердить выбор", callback_data=f"confirm_role_{role}"
    )
    keyboard.append([confirm_button])

    # Кнопка возврата к выбору
    back_button = InlineKeyboardButton(
        text="🔄 Выбрать другую роль", callback_data="back_to_roles"
    )
    keyboard.append([back_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_role_info_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с информацией о ролях"""
    keyboard = []

    # Кнопки для получения информации о каждой роли
    roles_info = [
        ("👩‍🏫 Учитель", "info_teacher"),
        ("🏛 Администрация", "info_admin"),
        ("📈 Директор", "info_director"),
        ("👪 Родитель", "info_parent"),
        ("👨‍🎓 Ученик", "info_student"),
        ("🧑‍⚕️ Психолог", "info_psych"),
    ]

    # Размещаем кнопки по 2 в ряд
    for i in range(0, len(roles_info), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=roles_info[i][0], callback_data=roles_info[i][1]
            )
        )

        if i + 1 < len(roles_info):
            row.append(
                InlineKeyboardButton(
                    text=roles_info[i + 1][0],
                    callback_data=roles_info[i + 1][1],
                )
            )

        keyboard.append(row)

    # Кнопка начала онбординга
    start_button = InlineKeyboardButton(
        text="🚀 Начать онбординг", callback_data="start_onboarding"
    )
    keyboard.append([start_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
