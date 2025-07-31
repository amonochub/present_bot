from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.enums import ico


def tasks_board(tasks: list[Any], lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура со списком поручений"""
    rows = [
        [
            InlineKeyboardButton(
                f"{ico(task.status)} #{task.id} {task.title[:18]}",
                callback_data=f"task_{task.id}",
            )
        ]
        for task in tasks
    ]
    # Добавляем кнопку "Назад"
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def add_back(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Добавить кнопку "Назад" к существующим рядам"""
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
