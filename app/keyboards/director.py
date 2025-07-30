from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.db.enums import ico

def tasks_board(tasks, lang="ru"):
    """Клавиатура со списком поручений"""
    rows = [
        [InlineKeyboardButton(
            f"{ico(task.status)} #{task.id} {task.title[:18]}",
            callback_data=f"task_{task.id}"
        )]
        for task in tasks
    ]
    # Добавляем кнопку "Назад"
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def add_back(rows):
    """Добавить кнопку "Назад" к существующим рядам"""
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows) 