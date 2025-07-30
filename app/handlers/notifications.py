from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.db.notification import Notification, NotificationStatus
from app.services.notification_service import NotificationService
from app.keyboards.main_menu import menu

router = Router()

class NotificationFSM(StatesGroup):
    settings = State()

@router.message(Command("notifications"))
async def show_notifications(msg: Message):
    """Показывает уведомления пользователя"""
    async with AsyncSessionLocal() as session:
        # Получаем пользователя
        result = await session.execute(
            select(User).where(User.tg_id == msg.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await msg.answer("❌ Пользователь не найден")
            return
        
        # Получаем уведомления
        notifications = await NotificationService.get_user_notifications(
            user_id=user.id,
            limit=5,
            unread_only=True
        )
        
        if not notifications:
            await msg.answer("📭 У вас нет непрочитанных уведомлений")
            return
        
        # Формируем список уведомлений
        text = "🔔 **Ваши уведомления:**\n\n"
        keyboard = []
        
        for notification in notifications:
            status_icon = "🔴" if notification.status == NotificationStatus.SENT else "🟢"
            text += f"{status_icon} **{notification.title}**\n{notification.message}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Прочитано" if notification.status == NotificationStatus.SENT else "👁 Просмотрено",
                    callback_data=f"notification_read_{notification.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="notification_settings")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await msg.answer(text, parse_mode="Markdown", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("notification_read_"))
async def mark_notification_read(call: CallbackQuery):
    """Отмечает уведомление как прочитанное"""
    notification_id = int(call.data.split("_")[-1])
    
    success = await NotificationService.mark_as_read(notification_id)
    
    if success:
        await call.answer("✅ Уведомление отмечено как прочитанное")
        # Обновляем сообщение
        await call.message.edit_text(
            call.message.text + "\n\n✅ **Отмечено как прочитанное**",
            parse_mode="Markdown"
        )
    else:
        await call.answer("❌ Ошибка при обновлении уведомления")

@router.callback_query(F.data == "notification_settings")
async def notification_settings(call: CallbackQuery):
    """Показывает настройки уведомлений"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.tg_id == call.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await call.answer("❌ Пользователь не найден")
            return
        
        status_icon = "✅" if user.notifications_enabled else "❌"
        email_icon = "✅" if user.email_notifications else "❌"
        
        text = f"⚙️ **Настройки уведомлений**\n\n"
        text += f"{status_icon} Telegram уведомления: {'Включены' if user.notifications_enabled else 'Отключены'}\n"
        text += f"{email_icon} Email уведомления: {'Включены' if user.email_notifications else 'Отключены'}\n\n"
        text += "Выберите действие:"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔕 Отключить уведомления" if user.notifications_enabled else "🔔 Включить уведомления",
                    callback_data="toggle_notifications"
                )
            ],
            [
                InlineKeyboardButton(
                    "📧 Отключить email" if user.email_notifications else "📧 Включить email",
                    callback_data="toggle_email"
                )
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_notifications")]
        ]
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await call.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(call: CallbackQuery):
    """Переключает уведомления"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.tg_id == call.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await call.answer("❌ Пользователь не найден")
            return
        
        user.notifications_enabled = not user.notifications_enabled
        await session.commit()
        
        status = "включены" if user.notifications_enabled else "отключены"
        await call.answer(f"✅ Уведомления {status}")
        
        # Обновляем настройки
        await notification_settings(call)

@router.callback_query(F.data == "toggle_email")
async def toggle_email_notifications(call: CallbackQuery):
    """Переключает email уведомления"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.tg_id == call.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await call.answer("❌ Пользователь не найден")
            return
        
        user.email_notifications = not user.email_notifications
        await session.commit()
        
        status = "включены" if user.email_notifications else "отключены"
        await call.answer(f"✅ Email уведомления {status}")
        
        # Обновляем настройки
        await notification_settings(call)

@router.callback_query(F.data == "back_to_notifications")
async def back_to_notifications(call: CallbackQuery):
    """Возврат к списку уведомлений"""
    await show_notifications(call.message)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    """Возврат в главное меню"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.tg_id == call.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            await call.message.edit_text(
                "🏠 Главное меню",
                reply_markup=menu(user.role, "ru")
            )
        else:
            await call.message.edit_text("❌ Ошибка загрузки меню") 