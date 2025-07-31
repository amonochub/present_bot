import logging
from typing import Any, Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu
from app.repositories import psych_repo

router = Router()
logger = logging.getLogger(__name__)


# helper: get current user role
async def get_user_role(tg_id: int) -> Any:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


# ─────────── Входящие обращения ───────────
@router.callback_query(F.data == "psych_inbox")
async def view_inbox(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["psych", "super"]:
            await call.answer("Эта функция доступна только психологу", show_alert=True)
            return

        requests = await psych_repo.list_open()
        if not requests:
            txt = "📥 <b>Входящие обращения</b>\n\nНет новых обращений"
        else:
            txt = "📥 <b>Входящие обращения</b>\n\n" + "\n".join(
                f"📝 <b>#{r.id}</b> — {r.text[:100]}{'...' if len(r.text) > 100 else ''}\n"
                f"👤 От: {r.from_id}\n"
                f"📅 {r.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                for r in requests
            )
        if call.message is not None:
            await call.message.edit_text(txt, reply_markup=menu("psych", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении входящих обращений: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("psych_mark_done_"))
async def mark_request_done(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["psych", "super"]:
            await call.answer("Эта функция доступна только психологу", show_alert=True)
            return

        request_id = int(call.data.split("_")[-1])

        success = await psych_repo.mark_done(request_id)
        if success:
            await call.answer("Обращение отмечено как обработанное", show_alert=True)
            # Обновляем список обращений
            requests = await psych_repo.list_open()
            if not requests:
                txt = "📥 <b>Входящие обращения</b>\n\nНет новых обращений"
            else:
                txt = "📥 <b>Входящие обращения</b>\n\n" + "\n".join(
                    f"📝 <b>#{r.id}</b> — {r.text[:100]}{'...' if len(r.text) > 100 else ''}\n"
                    f"👤 От: {r.from_id}\n"
                    f"📅 {r.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    for r in requests
                )
            if call.message is not None:
                await call.message.edit_text(txt, reply_markup=menu("psych", "ru"))
        else:
            await call.answer("Ошибка при обработке обращения", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отметке обращения как обработанного: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# ─────────── Статистика ───────────
@router.callback_query(F.data == "psych_stats")
async def view_stats(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["psych", "super"]:
            await call.answer("Эта функция доступна только психологу", show_alert=True)
            return

        # Получаем статистику обращений
        all_requests = await psych_repo.list_all()
        open_requests = [r for r in all_requests if r.status == Status.open]
        done_requests = [r for r in all_requests if r.status == Status.done]

        stats_text = (
            "📊 <b>Статистика обращений</b>\n\n"
            f"📥 Всего обращений: {len(all_requests)}\n"
            f"🟡 Новых: {len(open_requests)}\n"
            f"🟢 Обработанных: {len(done_requests)}\n"
            f"📈 Процент обработки: {len(done_requests)/len(all_requests)*100:.1f}%"
            if all_requests
            else "📊 <b>Статистика обращений</b>\n\n"
            "📥 Всего обращений: 0\n"
            "🟡 Новых: 0\n"
            "🟢 Обработанных: 0\n"
            "📈 Процент обработки: 0%"
        )

        if call.message is not None:
            await call.message.edit_text(stats_text, reply_markup=menu("psych", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await call.answer("Произошла ошибка", show_alert=True)
