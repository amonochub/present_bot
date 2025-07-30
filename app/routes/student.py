from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.repositories import psych_repo

router = Router()


# пункт меню «🆘 Психолог»
@router.callback_query(F.data == "stu_help")
async def ask_help(call: CallbackQuery, lang: str):
    await call.message.edit_text(
        "🧑‍⚕️ *Психологическая помощь*\n"
        "Отправьте текст или голосовое сообщение.\n"
        "Ваше обращение увидит только школьный психолог.",
        parse_mode="Markdown",
    )
    # FSM не требуется: любое следующее сообщение — обращение
    await call.answer()


# ловим текст/voice
@router.message(F.content_type.in_({"voice", "text"}))
async def receive_help(msg: Message, lang: str):
    # остальные роли будут игнорировать этот хэндлер;
    # для простоты не проверяем роль.
    if msg.voice or msg.text:
        file_id = msg.voice.file_id if msg.voice else None
        text = msg.text.strip() if msg.text else None
        await psych_repo.psy_create(msg.from_user.id, text, file_id)
        await msg.answer("✅ Обращение направлено психологу. Спасибо за доверие!")
