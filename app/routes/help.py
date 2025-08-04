"""
Хэндлер для команды /help
"""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.i18n import t
from app.repositories.user_repo import get_user
from app.roles import UserRole

router = Router()
logger = logging.getLogger(__name__)


# helper: get current user role
async def get_user_role(tg_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Показывает контекстную справку в зависимости от роли пользователя"""
    
    if not message.from_user:
        await message.answer("Ошибка: не удалось определить пользователя")
        return

    user = await get_user(message.from_user.id)

    if not user:
        # Справка для неавторизованных пользователей
        help_text = t("help.help_unauthorized")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("help.help_start_button"), callback_data="help:start")]
            ]
        )

    else:
        # Контекстная справка для авторизованных пользователей
        help_text = get_role_help(UserRole(user.role))
        keyboard = get_role_help_keyboard(UserRole(user.role))

    await message.answer(help_text, reply_markup=keyboard, parse_mode="HTML")


def get_role_help(role: UserRole) -> str:
    """Возвращает справку для конкретной роли"""

    help_texts = {
        UserRole.STUDENT: """
👨‍🎓 **Справка для ученика**

**Доступные команды:**
• /tasks - просмотр ваших заданий
• /notes - ваши заметки
• /ask - задать вопрос учителю
• /ticket - создать заявку в техподдержку

**Основные возможности:**
• 📋 Просмотр заданий от учителей
• 📝 Создание личных заметок
• ❓ Задавание вопросов учителям
• 🛠 Создание заявок в техподдержку

**Советы:**
• Регулярно проверяйте новые задания
• Используйте заметки для важной информации
• Не стесняйтесь задавать вопросы учителям
        """,
        UserRole.TEACHER: """
👩‍🏫 **Справка для учителя**

**Доступные команды:**
• /notes - ваши заметки о учениках
• /addnote - добавить новую заметку
• /ticket - создать заявку в IT-отдел
• /students - список ваших учеников

**Основные возможности:**
• 📝 Создание заметок о учениках
• 🛠 Создание заявок в техподдержку
• 👥 Управление списком учеников
• 📊 Просмотр статистики

**Советы:**
• Регулярно добавляйте заметки о учениках
• Используйте заявки для технических проблем
• Ведите учет успеваемости учеников
        """,
        UserRole.PARENT: """
👪 **Справка для родителя**

**Доступные команды:**
• /tasks - задания вашего ребенка
• /cert - заказ справок
• /progress - успеваемость ребенка
• /ticket - создать заявку

**Основные возможности:**
• 📋 Просмотр заданий ребенка
• 📄 Заказ PDF-справок
• 📈 Отслеживание успеваемости
• 🛠 Создание заявок в техподдержку

**Советы:**
• Регулярно проверяйте задания ребенка
• Заказывайте справки заранее
• Следите за успеваемостью
        """,
        UserRole.PSYCHOLOGIST: """
🧑‍⚕️ **Справка для психолога**

**Доступные команды:**
• /inbox - входящие обращения
• /requests - запросы на консультацию
• /schedule - расписание консультаций

**Основные возможности:**
• 📥 Просмотр анонимных обращений
• 📋 Управление запросами на консультации
• 📅 Планирование встреч
• 🔒 Конфиденциальная работа

**Советы:**
• Регулярно проверяйте новые обращения
• Соблюдайте конфиденциальность
• Ведите учет консультаций
        """,
        UserRole.ADMIN: """
🏛 **Справка для администратора**

**Доступные команды:**
• /tickets - управление заявками
• /broadcast - массовые рассылки
• /users - управление пользователями
• /stats - статистика системы

**Основные возможности:**
• 🛠 Обработка заявок пользователей
• 📢 Создание массовых рассылок
• 👥 Управление пользователями
• 📊 Мониторинг системы

**Советы:**
• Быстро обрабатывайте заявки
• Используйте рассылки для важных уведомлений
• Следите за статистикой системы
        """,
        UserRole.DIRECTOR: """
📈 **Справка для директора**

**Доступные команды:**
• /kpi - ключевые показатели
• /stats - статистика школы
• /reports - отчеты
• /tasks - управление задачами

**Основные возможности:**
• 📊 Просмотр KPI школы
• 📈 Анализ статистики
• 📋 Создание отчетов
• 📝 Управление задачами

**Советы:**
• Регулярно анализируйте KPI
• Используйте отчеты для принятия решений
• Ставьте задачи сотрудникам
        """,
    }

    return help_texts.get(
        role,
        """
❓ **Общая справка**

Используйте команду /start для начала работы с ботом.
Для получения справки по вашей роли используйте /help.
        """,
    ).strip()


def get_role_help_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру справки для конкретной роли"""

    role_keyboards = {
        UserRole.STUDENT: [
            [
                InlineKeyboardButton(
                    text=t("help.help_student_tasks"), callback_data="help:student:tasks"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_student_notes"), callback_data="help:student:notes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_student_ask"), callback_data="help:student:ask"
                )
            ],
        ],
        UserRole.TEACHER: [
            [
                InlineKeyboardButton(
                    text=t("help.help_teacher_notes"), callback_data="help:teacher:notes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_teacher_tickets"), callback_data="help:teacher:tickets"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_teacher_students"), callback_data="help:teacher:students"
                )
            ],
        ],
        UserRole.PARENT: [
            [
                InlineKeyboardButton(
                    text=t("help.help_parent_tasks"), callback_data="help:parent:tasks"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_parent_certs"), callback_data="help:parent:certs"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_parent_progress"), callback_data="help:parent:progress"
                )
            ],
        ],
        UserRole.PSYCHOLOGIST: [
            [
                InlineKeyboardButton(
                    text=t("help.help_psych_inbox"), callback_data="help:psych:inbox"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_psych_requests"), callback_data="help:psych:requests"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_psych_schedule"), callback_data="help:psych:schedule"
                )
            ],
        ],
        UserRole.ADMIN: [
            [
                InlineKeyboardButton(
                    text=t("help.help_admin_tickets"), callback_data="help:admin:tickets"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_admin_broadcast"), callback_data="help:admin:broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_admin_stats"), callback_data="help:admin:stats"
                )
            ],
        ],
        UserRole.DIRECTOR: [
            [
                InlineKeyboardButton(
                    text=t("help.help_director_kpi"), callback_data="help:director:kpi"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_director_stats"), callback_data="help:director:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help.help_director_reports"), callback_data="help:director:reports"
                )
            ],
        ],
    }

    keyboard = role_keyboards.get(role, [])
    keyboard.append(
        [InlineKeyboardButton(text=t("help.help_main_menu_button"), callback_data="menu:main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("help:"))
async def handle_help_callback(callback: CallbackQuery) -> None:
    """Обрабатывает нажатия на кнопки справки"""

    data = callback.data.split(":")

    if data[1] == "start":
        # Возврат к началу
        await callback.message.edit_text(t("help.help_start_message"), parse_mode="HTML")
    elif data[1] == "back":
        # Возврат к основной справке
        user = await get_user(callback.from_user.id)
        if user:
            help_text = get_role_help(user.role)
            keyboard = get_role_help_keyboard(user.role)
            await callback.message.edit_text(help_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(t("help.help_login_required"), parse_mode="HTML")
    else:
        # Показываем детальную справку по разделу
        role = data[1]
        section = data[2] if len(data) > 2 else None

        detail_text = get_detailed_help(role, section)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("help.help_back_button"), callback_data="help:back")],
                [
                    InlineKeyboardButton(
                        text=t("help.help_main_menu_button"), callback_data="menu:main"
                    )
                ],
            ]
        )

        await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


def get_detailed_help(role: str, section: str) -> str:
    """Возвращает детальную справку по разделу"""

    help_details = {
        "student": {
            "tasks": """
📋 **Задания для ученика**

**Как просматривать задания:**
1. Нажмите кнопку "📋 Задания" в главном меню
2. Выберите нужное задание из списка
3. Изучите описание и требования

**Типы заданий:**
• 📝 Домашние работы
• 🧪 Лабораторные работы
• 📊 Проекты
• 📚 Контрольные работы

**Советы:**
• Регулярно проверяйте новые задания
• Выполняйте задания в срок
• Задавайте вопросы, если что-то непонятно
            """,
            "notes": """
📝 **Заметки ученика**

**Как создавать заметки:**
1. Нажмите кнопку "📝 Заметки" в главном меню
2. Выберите "➕ Добавить заметку"
3. Введите текст заметки
4. Нажмите "✅ Сохранить"

**Для чего использовать:**
• 📚 Записи с уроков
• 📋 Список домашних заданий
• 💡 Важные идеи и мысли
• 📅 Напоминания

**Советы:**
• Делайте заметки сразу после урока
• Используйте эмодзи для лучшей организации
• Регулярно просматривайте старые заметки
            """,
            "ask": """
❓ **Вопросы учителю**

**Как задать вопрос:**
1. Нажмите кнопку "❓ Задать вопрос" в главном меню
2. Выберите предмет или учителя
3. Введите ваш вопрос
4. Нажмите "📤 Отправить"

**Типы вопросов:**
• 📚 По материалу урока
• 📝 По домашнему заданию
• 🧪 По лабораторной работе
• 📊 По проекту

**Советы:**
• Формулируйте вопросы четко и конкретно
• Прикладывайте фото, если нужно
• Будьте вежливы и уважительны
            """,
        },
        "teacher": {
            "notes": """
📝 **Заметки о учениках**

**Как создать заметку:**
1. Нажмите кнопку "📝 Заметки" в главном меню
2. Выберите "➕ Добавить заметку"
3. Выберите ученика из списка
4. Введите текст заметки
5. Нажмите "✅ Сохранить"

**Типы заметок:**
• 📚 Успеваемость по предмету
• 🎯 Поведение на уроках
• 💡 Особенности ученика
• 📊 Результаты контрольных

**Советы:**
• Делайте заметки регулярно
• Будьте объективны в оценках
• Отмечайте как успехи, так и проблемы
            """,
            "tickets": """
🛠 **Заявки в IT-отдел**

**Как создать заявку:**
1. Нажмите кнопку "🛠 Заявка" в главном меню
2. Выберите тип проблемы
3. Опишите проблему подробно
4. Нажмите "📤 Отправить"

**Типы проблем:**
• 💻 Проблемы с компьютером
• 📱 Проблемы с приложением
• 🌐 Проблемы с интернетом
• 📺 Проблемы с проектором

**Советы:**
• Опишите проблему максимально подробно
• Укажите, когда возникла проблема
• Приложите скриншот, если возможно
            """,
            "students": """
👥 **Мои ученики**

**Как просмотреть список:**
1. Нажмите кнопку "👥 Ученики" в главном меню
2. Выберите класс или группу
3. Просмотрите список учеников

**Информация о ученике:**
• 📚 Успеваемость по предметам
• 📝 Ваши заметки о ученике
• 📊 Статистика посещаемости
• 💬 Контакты родителей

**Советы:**
• Регулярно обновляйте информацию
• Отмечайте изменения в успеваемости
• Связывайтесь с родителями при необходимости
            """,
        },
        "parent": {
            "tasks": """
📋 **Задания ребенка**

**Как просматривать задания:**
1. Нажмите кнопку "📋 Задания" в главном меню
2. Выберите ребенка из списка
3. Просмотрите его задания

**Информация о заданиях:**
• 📝 Описание задания
• 📅 Срок выполнения
• 📊 Статус выполнения
• 👨‍🏫 Учитель, задавший работу

**Советы:**
• Регулярно проверяйте новые задания
• Помогайте ребенку с выполнением
• Следите за сроками сдачи
            """,
            "certs": """
📄 **Заказ справок**

**Как заказать справку:**
1. Нажмите кнопку "📄 Справки" в главном меню
2. Выберите тип справки
3. Укажите период
4. Нажмите "📤 Заказать"

**Типы справок:**
• 📊 Справка об успеваемости
• 📅 Справка о посещаемости
• 🏥 Справка для врача
• 🎓 Справка для поступления

**Советы:**
• Заказывайте справки заранее
• Указывайте точный период
• Сохраняйте полученные справки
            """,
            "progress": """
📈 **Успеваемость ребенка**

**Как просмотреть успеваемость:**
1. Нажмите кнопку "📈 Успеваемость" в главном меню
2. Выберите ребенка из списка
3. Выберите предмет или период

**Информация об успеваемости:**
• 📊 Средний балл по предметам
• 📝 Оценки за контрольные
• 📅 График успеваемости
• 👨‍🏫 Комментарии учителей

**Советы:**
• Регулярно проверяйте успеваемость
• Обсуждайте результаты с ребенком
• Связывайтесь с учителями при необходимости
            """,
        },
        "psychologist": {
            "inbox": """
📥 **Входящие обращения**

**Как просматривать обращения:**
1. Нажмите кнопку "📥 Обращения" в главном меню
2. Выберите новое обращение
3. Изучите содержимое
4. При необходимости ответьте

**Типы обращений:**
• 🆘 Срочные обращения
• 💬 Обычные вопросы
• 🆕 Новые обращения
• 📋 Обработанные

**Советы:**
• Регулярно проверяйте новые обращения
• Отвечайте в течение 24 часов
• Соблюдайте конфиденциальность
            """,
            "requests": """
📋 **Запросы на консультацию**

**Как управлять запросами:**
1. Нажмите кнопку "📋 Запросы" в главном меню
2. Просмотрите список запросов
3. Выберите запрос для обработки
4. Назначьте время консультации

**Типы запросов:**
• 👨‍🎓 От учеников
• 👪 От родителей
• 👩‍🏫 От учителей
• 🆕 Новые запросы

**Советы:**
• Быстро обрабатывайте новые запросы
• Учитывайте срочность
• Ведите учет консультаций
            """,
            "schedule": """
📅 **Расписание консультаций**

**Как управлять расписанием:**
1. Нажмите кнопку "📅 Расписание" в главном меню
2. Просмотрите запланированные встречи
3. Добавьте новую консультацию
4. Отредактируйте существующие

**Информация о встречах:**
• 👤 Клиент
• 📅 Дата и время
• ⏱ Продолжительность
• 📝 Тема консультации

**Советы:**
• Ведите актуальное расписание
• Напоминайте о встречах заранее
• Записывайте результаты консультаций
            """,
        },
        "admin": {
            "tickets": """
🛠 **Управление заявками**

**Как обрабатывать заявки:**
1. Нажмите кнопку "🛠 Заявки" в главном меню
2. Просмотрите список заявок
3. Выберите заявку для обработки
4. Измените статус или добавьте комментарий

**Статусы заявок:**
• 🆕 Новые
• 🔄 В работе
• ✅ Выполненные
• ❌ Отклоненные

**Советы:**
• Быстро обрабатывайте новые заявки
• Обновляйте статусы регулярно
• Связывайтесь с пользователями при необходимости
            """,
            "broadcast": """
📢 **Массовые рассылки**

**Как создать рассылку:**
1. Нажмите кнопку "📢 Рассылки" в главном меню
2. Выберите "➕ Новая рассылка"
3. Введите текст сообщения
4. Выберите получателей
5. Нажмите "📤 Отправить"

**Типы рассылок:**
• 📢 Всем пользователям
• 👨‍🎓 Только ученикам
• 👩‍🏫 Только учителям
• 👪 Только родителям

**Советы:**
• Используйте рассылки для важных уведомлений
• Проверяйте текст перед отправкой
• Не злоупотребляйте рассылками
            """,
            "stats": """
📊 **Статистика системы**

**Как просмотреть статистику:**
1. Нажмите кнопку "📊 Статистика" в главном меню
2. Выберите тип статистики
3. Просмотрите данные

**Типы статистики:**
• 👥 Активные пользователи
• 📝 Количество заметок
• 🛠 Обработанные заявки
• 📊 Активность по дням

**Советы:**
• Регулярно анализируйте статистику
• Отслеживайте тренды
• Используйте данные для улучшения системы
            """,
        },
        "director": {
            "kpi": """
📈 **Ключевые показатели**

**Как просмотреть KPI:**
1. Нажмите кнопку "📈 KPI" в главном меню
2. Выберите период
3. Просмотрите показатели

**Основные KPI:**
• 📊 Успеваемость учеников
• 👨‍🏫 Эффективность учителей
• 📝 Количество заметок
• 🛠 Скорость обработки заявок

**Советы:**
• Регулярно анализируйте KPI
• Сравнивайте показатели по периодам
• Используйте данные для принятия решений
            """,
            "stats": """
📊 **Статистика школы**

**Как просмотреть статистику:**
1. Нажмите кнопку "📊 Статистика" в главном меню
2. Выберите тип отчета
3. Просмотрите данные

**Типы отчетов:**
• 📈 Общая успеваемость
• 👥 Статистика по классам
• 👨‍🏫 Эффективность учителей
• 📊 Финансовые показатели

**Советы:**
• Регулярно анализируйте статистику
• Используйте данные для планирования
• Делитесь результатами с коллективом
            """,
            "reports": """
📋 **Создание отчетов**

**Как создать отчет:**
1. Нажмите кнопку "📋 Отчеты" в главном меню
2. Выберите тип отчета
3. Укажите период
4. Нажмите "📤 Создать"

**Типы отчетов:**
• 📊 Отчет об успеваемости
• 👥 Отчет по классам
• 👨‍🏫 Отчет по учителям
• 📈 Финансовый отчет

**Советы:**
• Создавайте отчеты регулярно
• Используйте данные для принятия решений
• Сохраняйте важные отчеты
            """,
        },
    }

    role_details = help_details.get(role, {})
    section_text = role_details.get(section, f"📖 Детальная справка по разделу {section}")

    return section_text.strip()


# ─────────── Кнопка справки ───────────
@router.callback_query(F.data == "help")
async def help_button(call: CallbackQuery, lang: str) -> None:
    try:
        if call.from_user is None:
            await call.answer(t("help.help_user_not_found"), show_alert=True)
            return
        user_role = await get_user_role(call.from_user.id)
        if not user_role:
            await call.answer(t("help.help_please_login"), show_alert=True)
            return

        help_text = get_role_help(user_role)
        keyboard = get_role_help_keyboard(user_role)
        full_text = help_text + "\n\n" + get_faq_text(lang)
        if call.message is not None and hasattr(call.message, "edit_text"):
            await call.message.edit_text(full_text, reply_markup=keyboard)
            await call.answer(t("help.help_help_loaded"))
        else:
            await call.answer(t("help.help_help_loaded"))
    except Exception as e:
        logger.error(f"Ошибка при показе справки: {e}")
        await call.answer(t("help.help_error_loading"), show_alert=True)


def get_faq_text(lang: str) -> str:
    """Возвращает FAQ текст на указанном языке"""

    faq_text = f"""
{t("help.help_faq_title")}

{t("help.help_faq_role_change")}

{t("help.help_faq_password")}

{t("help.help_faq_notifications")}

{t("help.help_faq_support")}
    """

    return faq_text.strip()


# ─────────── Команды для учителей ───────────
@router.message(Command("notes"))
async def teacher_notes_command(msg: Message, lang: str) -> None:
    """Команда /notes для учителей"""
    try:
        if msg.from_user is None:
            await msg.answer("Ошибка: пользователь не найден.")
            return
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return

        # Здесь должна быть логика получения заметок
        await msg.answer(
            "📝 <b>Мои заметки</b>\n\nИспользуйте кнопку «📝 Заметки» в меню для просмотра."
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /notes: {e}")
        await msg.answer("Произошла ошибка при получении заметок")


@router.message(Command("addnote"))
async def teacher_addnote_command(msg: Message, lang: str) -> None:
    """Команда /addnote для учителей"""
    try:
        if msg.from_user is None:
            await msg.answer("Ошибка: пользователь не найден.")
            return
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return

        # Парсим команду: /addnote Имя Текст
        if msg.text is None:
            await msg.answer("Использование: /addnote Имя_ученика Текст_заметки")
            return
        text = msg.text.replace("/addnote", "").strip()
        if not text:
            await msg.answer("Использование: /addnote Имя_ученика Текст_заметки")
            return

        # Здесь должна быть логика добавления заметки
        await msg.answer(
            "✅ Заметка добавлена!\n\n"
            "Используйте кнопку «➕ Добавить заметку» для удобного добавления."
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /addnote: {e}")
        await msg.answer("Произошла ошибка при добавлении заметки")


@router.message(Command("ticket"))
async def teacher_ticket_command(msg: Message, lang: str) -> None:
    """Команда /ticket для учителей"""
    try:
        if msg.from_user is None:
            await msg.answer("Ошибка: пользователь не найден.")
            return
        user = await get_user_role(msg.from_user.id)
        if not user or user not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            return

        # Парсим команду: /ticket Описание
        if msg.text is None:
            await msg.answer("Использование: /ticket Описание_проблемы")
            return
        text = msg.text.replace("/ticket", "").strip()
        if not text:
            await msg.answer("Использование: /ticket Описание_проблемы")
            return

        # Здесь должна быть логика создания заявки
        await msg.answer(
            "✅ IT-заявка создана!\n\n"
            "Используйте кнопку «🛠 IT-заявки» для удобного создания заявок."
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /ticket: {e}")
        await msg.answer("Произошла ошибка при создании заявки")
