from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.i18n import t
from app.keyboards.main_menu import menu
from app.repositories.user_repo import get_user, update_user_intro

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
        "text": "Обрабатывает заявки IT и управляет массовыми рассылками",
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
        "text": "Принимает анонимные обращения и ведет консультации",
        "icon": "🧑‍⚕️",
    },
]


async def send_intro_slide(msg: Message, idx: int, lang: str = "ru") -> None:
    """Отправляет слайд онбординга"""
    slide = INTRO_SLIDES[idx]
    text = f"{slide['icon']} <b>{slide['title']}</b>\n\n{slide['text']}"

    # Формируем клавиатуру с кнопками навигации
    keyboard = []
    if idx > 0:
        keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="intro_prev")])
    if idx < len(INTRO_SLIDES) - 1:
        keyboard.append([InlineKeyboardButton(text="➡️ Дальше", callback_data="intro_next")])
    else:
        keyboard.append([InlineKeyboardButton(text="🚀 Готово!", callback_data="intro_done")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await msg.answer(text, parse_mode="HTML", reply_markup=reply_markup)


@router.message(Command("start"))
async def start_with_intro(msg: Message, state: FSMContext, lang: str = "ru") -> None:
    """Обработчик команды /start с проверкой онбординга"""
    user = await get_user(msg.from_user.id)

    if not user.seen_intro:
        # Показываем онбординг
        await state.set_state("IntroFSM:idx")
        await state.update_data(idx=0)
        await send_intro_slide(msg, 0, lang)
    else:
        # Показываем обычное меню
        await msg.answer(t("common.welcome", lang), reply_markup=menu(user.role, lang))


@router.callback_query(F.data == "intro_next")
async def intro_next(callback: CallbackQuery, state: FSMContext, lang: str = "ru") -> None:
    """Следующий слайд онбординга"""
    data = await state.get_data()
    idx = data.get("idx", 0)

    if idx < len(INTRO_SLIDES) - 1:
        if callback.message:
            await callback.message.delete()
        await state.update_data(idx=idx + 1)
        if callback.message:
            await send_intro_slide(callback.message, idx + 1, lang)

    await callback.answer()


@router.callback_query(F.data == "intro_prev")
async def intro_prev(callback: CallbackQuery, state: FSMContext, lang: str = "ru") -> None:
    """Предыдущий слайд онбординга"""
    data = await state.get_data()
    idx = data.get("idx", 0)

    if idx > 0:
        if callback.message:
            await callback.message.delete()
        await state.update_data(idx=idx - 1)
        if callback.message:
            await send_intro_slide(callback.message, idx - 1, lang)

    await callback.answer()


@router.callback_query(F.data == "intro_done")
async def intro_done(callback: CallbackQuery, state: FSMContext, lang: str = "ru") -> None:
    """Завершение онбординга"""
    # Обновляем статус пользователя
    await update_user_intro(callback.from_user.id, True)

    # Очищаем состояние
    await state.clear()

    # Показываем основное меню
    user = await get_user(callback.from_user.id)
    if callback.message:
        await callback.message.delete()
        await callback.message.answer(t("common.welcome", lang), reply_markup=menu(user.role, lang))

    await callback.answer()
