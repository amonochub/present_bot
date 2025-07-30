from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu

router = Router()

# Слайды онбординга
INTRO_SLIDES = [
    {
        "title": "👩‍🏫 Учитель",
        "text": "Добавляет заметки о учениках и создает заявки в IT-отдел",
        "icon": "👩‍🏫",
    },
    {
        "title": "🏛 Администрация",
        "text": "Обрабатывает заявки IT, управляет массовыми рассылками",
        "icon": "🏛",
    },
    {
        "title": "📈 Директор",
        "text": "Следит за KPI, дает поручения и анализирует статистику",
        "icon": "📈",
    },
    {
        "title": "👨‍🎓 Ученик",
        "text": "Просматривает задания, может задать вопрос учителю",
        "icon": "👨‍🎓",
    },
    {
        "title": "👪 Родитель",
        "text": "Заказывает PDF-справки и следит за успеваемостью ребенка",
        "icon": "👪",
    },
    {
        "title": "🧑‍⚕️ Психолог",
        "text": "Принимает анонимные обращения и отмечает решенные вопросы",
        "icon": "🧑‍⚕️",
    },
]


class IntroFSM(StatesGroup):
    idx = State()


async def mark_intro_seen(tg_id: int):
    """Отмечает, что пользователь прошел онбординг"""
    async with AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.tg_id == tg_id).values(seen_intro=True))
        await s.commit()


async def get_user(tg_id: int) -> User:
    """Получает пользователя из БД"""
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()


async def send_intro_slide(msg: Message, idx: int, lang: str = "ru"):
    """Отправляет слайд онбординга"""
    if idx >= len(INTRO_SLIDES):
        return False

    slide = INTRO_SLIDES[idx]

    # Формируем текст слайда
    text = f"{slide['icon']} <b>{slide['title']}</b>\n\n{slide['text']}"

    # Формируем клавиатуру
    keyboard = []

    if idx > 0:
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="intro_prev")])

    if idx < len(INTRO_SLIDES) - 1:
        keyboard.append([InlineKeyboardButton("➡️ Дальше", callback_data="intro_next")])
    else:
        keyboard.append([InlineKeyboardButton("🚀 Готово!", callback_data="intro_done")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await msg.answer(text, parse_mode="HTML", reply_markup=reply_markup)
    return True


@router.message(Command("start"))
async def start_with_intro(msg: Message, state, lang: str = "ru"):
    """Обработчик команды /start с проверкой онбординга"""
    user = await get_user(msg.from_user.id)

    if not user:
        # Создаем нового пользователя
        user = User(
            tg_id=msg.from_user.id,
            username=msg.from_user.username,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name,
            role="student",  # Дефолтная роль
            seen_intro=False,
        )
        async with AsyncSessionLocal() as s:
            s.add(user)
            await s.commit()

    if not user.seen_intro:
        # Показываем онбординг
        await state.set_state(IntroFSM.idx)
        await state.update_data(idx=0)
        await send_intro_slide(msg, 0, lang)
    else:
        # Показываем обычное меню
        await msg.answer(
            f"👋 Привет, {msg.from_user.first_name or 'пользователь'}!\n\n" "Выберите действие:",
            reply_markup=menu(user.role, lang),
        )


@router.callback_query(F.data == "intro_next")
async def intro_next(call: CallbackQuery, state, lang: str = "ru"):
    """Следующий слайд онбординга"""
    data = await state.get_data()
    idx = data.get("idx", 0) + 1

    await state.update_data(idx=idx)

    # Удаляем предыдущее сообщение
    await call.message.delete()

    # Отправляем новый слайд
    await send_intro_slide(call.message, idx, lang)
    await call.answer()


@router.callback_query(F.data == "intro_prev")
async def intro_prev(call: CallbackQuery, state, lang: str = "ru"):
    """Предыдущий слайд онбординга"""
    data = await state.get_data()
    idx = max(0, data.get("idx", 0) - 1)

    await state.update_data(idx=idx)

    # Удаляем предыдущее сообщение
    await call.message.delete()

    # Отправляем новый слайд
    await send_intro_slide(call.message, idx, lang)
    await call.answer()


@router.callback_query(F.data == "intro_done")
async def intro_done(call: CallbackQuery, state, lang: str = "ru"):
    """Завершение онбординга"""
    # Отмечаем, что пользователь прошел онбординг
    await mark_intro_seen(call.from_user.id)

    # Очищаем состояние
    await state.clear()

    # Получаем обновленного пользователя
    user = await get_user(call.from_user.id)

    # Удаляем последнее сообщение онбординга
    await call.message.delete()

    # Показываем главное меню
    await call.message.answer(
        "🎉 Отлично! Теперь вы знаете основные возможности бота.\n\n" "Выберите действие:",
        reply_markup=menu(user.role, lang),
    )
    await call.answer()
