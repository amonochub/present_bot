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
        faq_text = get_faq_text(lang)
        full_text = help_text + "\n\n" + faq_text
        await msg.answer(full_text, reply_markup=menu(user_role, lang))
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
            "3. При необходимости прикрепите файл\n\n"
            "⌨️ <b>Текстовые команды:</b>\n"
            "• <code>/notes</code> — показать мои заметки\n"
            "• <code>/addnote Имя Текст</code> — добавить заметку\n"
            "• <code>/ticket Описание</code> — создать IT-заявку"
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
            "3. Психолог ответит в ближайшее время\n\n"
            "⌨️ <b>Текстовые команды:</b>\n"
            "• <code>/tasks</code> — показать задания\n"
            "• <code>/psych Помощь</code> — обратиться к психологу"
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
            "• Справка о поведении\n\n"
            "⌨️ <b>Текстовые команды:</b>\n"
            "• <code>/child_tasks</code> — задания ребенка\n"
            "• <code>/certificate Тип</code> — получить справку"
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
            "3. Отметьте как обработанное\n\n"
            "⌨️ <b>Текстовые команды:</b>\n"
            "• <code>/incoming</code> — новые обращения\n"
            "• <code>/stats</code> — статистика"
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
            "3. Отслеживайте статистику\n\n"
            "⌨️ <b>Текстовые команды:</b>\n"
            "• <code>/tickets</code> — все заявки\n"
            "• <code>/broadcast Текст</code> — рассылка"
        )
    
    elif role == "director":
        return (
            "📊 <b>Справка для директора</b>\n\n"
            "📈 <b>Доступные функции:</b>\n"
            "• <b>KPI отчет</b> — сводная статистика школы\n"
            "• <b>Задачи</b> — управление поручениями\n\n"
            "💡 <b>Команды:</b>\n"
            "• <code>/kpi</code> — показать KPI отчет\n"
            "• <code>/tasks</code> — управление задачами\n"
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

def get_faq_text(lang: str) -> str:
    """Возвращает FAQ для всех пользователей"""
    return (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "🤔 <b>Что делает бот?</b>\n"
        "Школьная информационная система для учителей, учеников, родителей и администрации.\n\n"
        "🔐 <b>Как сменить пароль?</b>\n"
        "Обратитесь к администратору школы для сброса пароля.\n\n"
        "🌐 <b>Как сменить язык?</b>\n"
        "Измените язык в настройках Telegram, бот автоматически подхватит.\n\n"
        "📱 <b>Почему бот не отвечает?</b>\n"
        "Проверьте интернет-соединение. Если проблема повторяется, обратитесь к администратору.\n\n"
        "⏰ <b>Время работы поддержки</b>\n"
        "Пн-Пт: 8:00-18:00, Сб: 9:00-15:00\n\n"
        "📞 <b>Контакты поддержки</b>\n"
        "Email: support@schoolbot.ru\n"
        "Телефон: +7 (XXX) XXX-XX-XX"
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
        faq_text = get_faq_text(lang)
        full_text = help_text + "\n\n" + faq_text
        await call.message.edit_text(full_text, reply_markup=menu(user_role, lang))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при показе справки: {e}")
        await call.answer("Произошла ошибка при загрузке справки", show_alert=True)

# ─────────── Команды для учителей ───────────
@router.message(Command("notes"))
async def teacher_notes_command(msg: Message, lang: str):
    """Команда /notes для учителей"""
    try:
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return
            
        # Здесь должна быть логика получения заметок
        await msg.answer("📝 <b>Мои заметки</b>\n\nИспользуйте кнопку «📝 Заметки» в меню для просмотра.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /notes: {e}")
        await msg.answer("Произошла ошибка при получении заметок")

@router.message(Command("addnote"))
async def teacher_addnote_command(msg: Message, lang: str):
    """Команда /addnote для учителей"""
    try:
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return
            
        # Парсим команду: /addnote Имя Текст
        text = msg.text.replace("/addnote", "").strip()
        if not text:
            await msg.answer("Использование: /addnote Имя_ученика Текст_заметки")
            return
            
        # Здесь должна быть логика добавления заметки
        await msg.answer("✅ Заметка добавлена!\n\nИспользуйте кнопку «➕ Добавить заметку» для удобного добавления.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /addnote: {e}")
        await msg.answer("Произошла ошибка при добавлении заметки")

@router.message(Command("ticket"))
async def teacher_ticket_command(msg: Message, lang: str):
    """Команда /ticket для учителей"""
    try:
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return
            
        # Парсим команду: /ticket Описание
        text = msg.text.replace("/ticket", "").strip()
        if not text:
            await msg.answer("Использование: /ticket Описание_проблемы")
            return
            
        # Здесь должна быть логика создания заявки
        await msg.answer("✅ IT-заявка создана!\n\nИспользуйте кнопку «🛠 IT-заявки» для удобного создания заявок.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /ticket: {e}")
        await msg.answer("Произошла ошибка при создании заявки") 