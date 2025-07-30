from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from app.keyboards.main_menu import menu
from app.services.pdf_factory import make_certificate

router = Router()

class CertFSM(StatesGroup):
    waiting_type = State()

# пункт меню
@router.callback_query(F.data == "par_cert")
async def ask_type(call: CallbackQuery, state):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Об обучении", callback_data="cert_school")],
        [InlineKeyboardButton("О составе семьи", callback_data="cert_family")],
        [InlineKeyboardButton("◀️ Назад", callback_data="stub")],
    ])
    await call.message.edit_text("Выберите тип справки:", reply_markup=kb)
    await state.set_state(CertFSM.waiting_type)
    await call.answer()

# кликаем тип справки
@router.callback_query(CertFSM.waiting_type,
                       lambda c: c.data.startswith("cert_"))
async def make_cert(call: CallbackQuery, state):
    cert_type = call.data.split("_", 1)[1]  # school | family
    pdf_io = make_certificate(cert_type)
    await call.message.answer_document(
        InputFile(pdf_io, filename="spravka.pdf"),
        caption="Готово! Справка сформирована."
    )
    await state.clear()
    await call.message.answer("Меню родителя:", reply_markup=menu("parent"))
    await call.answer() 