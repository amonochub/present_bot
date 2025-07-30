"""
Хэндлер для команды /help
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from typing import Optional
import logging
from app.keyboards.main_menu import menu
from app.db.user import User
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.i18n import t

router = Router()
logger = logging.getLogger(__name__)

# helper: get current user role
async def get_user_role(tg_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None

# ─────────── Команда /help ───────────
@router.message(Command("help"))
async def help_command(msg: Message, lang: str):
    try:
        user_role = await get_user_role(msg.from_user.id)
        if not user_role:
            await msg.answer("Пожалуйста, сначала войдите в систему.")
            return
            
        help_text = get_help_text(user_role, lang)
        await msg.answer(help_text, reply_markup=menu(user_role, lang))
    except Exception as e:
        logger.error(f"Ошибка при показе справки: {e}")
        await msg.answer("Произошла ошибка при загрузке справки")

def get_help_text(role: str, lang: str) -> str:
    """Возвращает текст справки в зависимости от роли пользователя"""
    
    if role == "teacher":
        return (
            "👩‍🏫 <b>Справка для учителя</b>\n\n"
            "📝 <b>Доступные функции:</b>\n"
            "• <b>Заметки</b> — создание и просмотр заметок о учениках\n"
            "• <b>IT-заявки</b> — подача заявок в техподдержку\n"
            "• <b>Медиа-заявки</b> — заявки в медиацентр\n\n"
            "💡 <b>Как добавить заметку:</b>\n"
            "1. Нажмите «➕ Добавить заметку»\n"
            "2. Введите в формате: <code>Имя ученика Текст заметки</code>\n\n"
            "💡 <b>Как создать заявку:</b>\n"
            "1. Выберите тип заявки (IT или медиа)\n"
            "2. Введите описание проблемы\n"
            "3. При необходимости прикрепите файл"
        )
    
    elif role == "student":
        return (
            "👨‍🎓 <b>Справка для ученика</b>\n\n"
            "📚 <b>Доступные функции:</b>\n"
            "• <b>Задания</b> — просмотр домашних заданий и поручений\n"
            "• <b>Помощь психолога</b> — обращение к школьному психологу\n\n"
            "💡 <b>Как обратиться к психологу:</b>\n"
            "1. Нажмите «🆘 Психолог»\n"
            "2. Напишите ваш вопрос или проблему\n"
            "3. Психолог ответит в ближайшее время"
        )
    
    elif role == "parent":
        return (
            "👪 <b>Справка для родителя</b>\n\n"
            "📚 <b>Доступные функции:</b>\n"
            "• <b>Задания ребенка</b> — просмотр заданий вашего ребенка\n"
            "• <b>Справки</b> — получение различных справок\n\n"
            "💡 <b>Доступные справки:</b>\n"
            "• Справка о посещаемости\n"
            "• Справка об успеваемости\n"
            "• Справка о поведении"
        )
    
    elif role == "psych":
        return (
            "🧑‍⚕️ <b>Справка для психолога</b>\n\n"
            "📥 <b>Доступные функции:</b>\n"
            "• <b>Входящие обращения</b> — просмотр новых обращений от учеников\n"
            "• <b>Статистика</b> — статистика обращений\n\n"
            "💡 <b>Как работать с обращениями:</b>\n"
            "1. Просмотрите список новых обращений\n"
            "2. Обработайте каждое обращение\n"
            "3. Отметьте как обработанное"
        )
    
    elif role == "admin":
        return (
            "🏛 <b>Справка для администратора</b>\n\n"
            "📋 <b>Доступные функции:</b>\n"
            "• <b>Заявки техподдержки</b> — управление IT-заявками\n"
            "• <b>Медиа-заявки</b> — управление заявками медиацентра\n"
            "• <b>Рассылка</b> — массовая рассылка сообщений\n\n"
            "💡 <b>Как управлять заявками:</b>\n"
            "1. Просмотрите список заявок\n"
            "2. Измените статус на «В работе» или «Выполнено»\n"
            "3. Отслеживайте статистику"
        )
    
    elif role == "director":
        return (
            "📊 <b>Справка для директора</b>\n\n"
            "📈 <b>Доступные функции:</b>\n"
            "• <b>KPI отчет</b> — сводная статистика школы\n"
            "• <b>Задачи</b> — управление поручениями\n\n"
            "💡 <b>Команды:</b>\n"
            "• <code>/kpi</code> — показать KPI отчет\n"
            "• <code>/help</code> — показать эту справку\n\n"
            "📊 <b>KPI включает:</b>\n"
            "• Количество заметок учителей\n"
            "• Статистика заявок и их выполнения\n"
            "• Количество задач и просроченных"
        )
    
    else:
        return (
            "❓ <b>Общая справка</b>\n\n"
            "Добро пожаловать в школьную информационную систему!\n\n"
            "💡 <b>Основные команды:</b>\n"
            "• <code>/start</code> — начать работу\n"
            "• <code>/help</code> — показать справку\n"
            "• <code>/theme</code> — изменить тему\n\n"
            "🔧 <b>Поддержка:</b>\n"
            "При возникновении проблем обратитесь к администратору системы."
        )

# ─────────── Кнопка справки ───────────
@router.callback_query(F.data == "help")
async def help_button(call: CallbackQuery, lang: str):
    try:
        user_role = await get_user_role(call.from_user.id)
        if not user_role:
            await call.answer("Пожалуйста, сначала войдите в систему.", show_alert=True)
            return
            
        help_text = get_help_text(user_role, lang)
        await call.message.edit_text(help_text, reply_markup=menu(user_role, lang))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при показе справки: {e}")
        await call.answer("Произошла ошибка при загрузке справки", show_alert=True) 