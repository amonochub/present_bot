from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import get_back_btn, menu

router = Router()

TOUR_ROLES = ["teacher", "admin", "director", "student", "parent", "psych"]


class TourFSM(StatesGroup):
    step = State()


async def set_role(tg_id: int, role: str):
    async with AsyncSessionLocal() as s:
        await s.execute(
            select(User)
            .where(User.tg_id == tg_id)
            .execution_options(populate_existing=True)
        )
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        user.role = role
        await s.commit()


def _tour_text(role: str) -> str:
    mapping = {
        "teacher": "👩‍🏫 <b>Учитель</b>\nДобавляет заметки, заявки IT, запросы в медиацентр.",
        "admin": "🏛 <b>Администрация</b>\nКанбан заявок, массовые рассылки учителям.",
        "director": "📈 <b>Директор</b>\nСмотрит KPI, даёт поручения.",
        "student": "👨‍🎓 <b>Ученик</b>\nВидит задания, может задать вопрос учителю.",
        "parent": "👪 <b>Родитель</b>\nЗаказывает PDF-справки, следит за заданиями.",
        "psych": "🧑‍⚕️ <b>Психолог</b>\nПринимает обращения, отмечает «Решено».",
    }
    return mapping[role]


# ───────────── /tour ─────────────
@router.message(Command("tour"))
async def start_tour(msg: Message, state, lang: str):
    await state.set_state(TourFSM.step)
    await state.update_data(idx=0)
    await next_step(msg, state, lang)


# ───────────── «Дальше» ─────────────
@router.callback_query(lambda c: c.data == "tour_next")
async def next_cb(call: CallbackQuery, state, lang: str):
    await next_step(call.message, state, lang)
    await call.answer()


# ───────────── «Главное меню» ─────────────
@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_cb(call: CallbackQuery, state, lang: str):
    await state.clear()
    await call.message.edit_text(
        "🏠 Вы вернулись в демо-меню", reply_markup=menu("super", lang)
    )
    await call.answer()


async def next_step(msg: Message, state, lang: str):
    data = await state.get_data()
    idx = data.get("idx", 0)

    if idx >= len(TOUR_ROLES):
        await state.clear()
        await msg.answer(
            "🚀 Тур завершён! Вы снова в демо-меню.", reply_markup=menu("super", lang)
        )
        return

    role = TOUR_ROLES[idx]
    await set_role(msg.from_user.id, role)  # «переключаем» роль

    # отправляем пояснение и меню роли
    await msg.answer(_tour_text(role), parse_mode="HTML", reply_markup=menu(role, lang))
    # добавляем кнопку «Дальше»
    next_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("➡️ Дальше", callback_data="tour_next")],
            get_back_btn(),  # позволяет выйти в любой момент
        ]
    )
    await msg.answer(
        "Переключайтесь по меню или нажмите «Дальше» →", reply_markup=next_btn
    )

    await state.update_data(idx=idx + 1)
