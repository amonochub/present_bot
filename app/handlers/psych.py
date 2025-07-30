from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.keyboards.main_menu import menu
from app.repositories import psych_repo

router = Router()


# список открытых обращений
@router.callback_query(F.data == "psy_inbox")
async def inbox(call: CallbackQuery, lang: str):
    reqs = await psych_repo.psy_list()
    if not reqs:
        await call.message.edit_text(
            t("psych.requests_empty", lang), reply_markup=menu("psych", lang)
        )
        await call.answer()
        return
    lines = [f"• #{r.id} — голосовое" if r.content_id else f"• #{r.id} — текст" for r in reqs]
    txt = (
        "📥 <b>Новые обращения</b>\n\n"
        + "\n".join(lines)
        + "\n\nВведите <code>/take id</code> чтобы открыть."
    )
    await call.message.edit_text(txt, reply_markup=menu("psych", lang))
    await call.answer()


# команда /take
@router.message(F.text.startswith("/take"))
async def take(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("Формат: /take 3")
        return
    req_id = int(parts[1])
    reqs = await psych_repo.psy_list()
    req = next((r for r in reqs if r.id == req_id), None)
    if not req:
        await msg.answer("⛔️ Нет открытого обращения с таким номером.")
        return
    if req.content_id:
        # голосовое
        await msg.answer_voice(req.content_id, caption=f"Обращение #{req.id}")
    if req.text:
        await msg.answer(f"#{req.id} — {req.text}")
    await msg.answer("Чтобы отметить обращение решённым — /done id")


# команда /done
@router.message(F.text.startswith("/done"))
async def done(msg: Message, lang: str):
    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("Формат: /done 3")
        return
    await psych_repo.mark_done(int(parts[1]))
    await msg.answer("✅ Помечено как решённое!")
