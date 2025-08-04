"""
Роутер для работы с документами и новостями с улучшениями Context7
"""

import logging
from typing import List

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.i18n import t
from app.repositories.user_repo import get_user
from app.roles import UserRole
from app.services.news_parser import get_news_cards

router = Router()
logger = logging.getLogger(__name__)


def get_localized_text(key: str, **kwargs) -> str:
    """Получить локализованный текст с подстановкой параметров согласно Context7"""
    text = t(key)
    if kwargs:
        return text.format(**kwargs)
    return text


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    """Обработка ошибок на уровне роутера согласно Context7"""
    logger.error(f"Ошибка в docs роутере: {event.exception}", exc_info=True)

    # Отправляем уведомление пользователю если возможно
    if hasattr(event, "update") and hasattr(event.update, "message"):
        try:
            await event.update.message.answer(
                "⚠️ Произошла ошибка при обработке запроса. Попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")


@router.message(Command("docs"))
async def show_docs(message: Message) -> None:
    """Показать список доступных документов"""
    try:
        user = await get_user(message.from_user.id)

        # Проверяем доступ к документам
        if not user:
            await message.answer("❌ Для доступа к документам необходимо войти в систему")
            return

        # Создаем клавиатуру с документами
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Психологическая помощь", callback_data="doc_standard")],
                [InlineKeyboardButton(text="Оплата труда", callback_data="doc_pay")],
                [InlineKeyboardButton(text="Службы помощи", callback_data="doc_help")],
            ]
        )

        # Формируем текст с улучшенной локализацией согласно Context7
        text = (
            f"{get_localized_text('docs.list_header')}\n"
            f"{get_localized_text('docs.item_standard')}\n"
            f"{get_localized_text('docs.item_pay')}\n"
            f"{get_localized_text('docs.item_help')}\n\n"
            f"{get_localized_text('docs.reply_footer')}"
        )

        await message.answer(text, reply_markup=kb)

    except Exception as e:
        logger.error(f"Ошибка при показе документов: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при загрузке документов")


@router.callback_query(F.data.startswith("doc_"))
async def send_doc_link(callback: CallbackQuery) -> None:
    """Отправить ссылку на документ"""
    try:
        doc_map = {
            "doc_standard": {
                "title": "Порядок оказания психолого-педагогической помощи",
                "description": "Приказ ДОНМ №___ о порядке оказания психолого-педагогической помощи обучающимся",
                "url": "https://www.mos.ru/donm/documents/",
                "file_url": "https://www.mos.ru/donm/documents/order_psych_help.pdf",
            },
            "doc_pay": {
                "title": "Методика оплаты труда педагогических работников",
                "description": "Методические рекомендации по оплате труда педагогических работников",
                "url": "https://www.mos.ru/donm/documents/",
                "file_url": "https://www.mos.ru/donm/documents/payment_methodology.pdf",
            },
            "doc_help": {
                "title": "Официальные службы помощи",
                "description": "Контакты и информация о службах психологической помощи",
                "url": "https://www.dpomos.ru/",
                "file_url": "https://www.dpomos.ru/contacts",
            },
        }

        doc_key = callback.data
        if doc_key in doc_map:
            doc_info = doc_map[doc_key]

            text = (
                f"📄 **{doc_info['title']}**\n\n"
                f"{doc_info['description']}\n\n"
                f"🔗 **Ссылка на документ:**\n{doc_info['url']}\n\n"
                f"📎 **Прямая ссылка:**\n{doc_info['file_url']}"
            )

            # Создаем клавиатуру с кнопками
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📄 Открыть документ", url=doc_info["url"])],
                    [InlineKeyboardButton(text="📎 Скачать", url=doc_info["file_url"])],
                    [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="docs_back")],
                ]
            )

            if callback.message and hasattr(callback.message, "edit_text"):
                await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            if callback.message and hasattr(callback.message, "answer"):
                await callback.message.answer(get_localized_text("docs.unknown_doc"))

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при отправке документа: {e}", exc_info=True)
        await callback.answer("⚠️ Произошла ошибка при загрузке документа", show_alert=True)


@router.callback_query(F.data == "docs_back")
async def back_to_docs_list(callback: CallbackQuery) -> None:
    """Вернуться к списку документов"""
    try:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Психологическая помощь", callback_data="doc_standard")],
                [InlineKeyboardButton(text="Оплата труда", callback_data="doc_pay")],
                [InlineKeyboardButton(text="Службы помощи", callback_data="doc_help")],
            ]
        )

        text = (
            f"{get_localized_text('docs.list_header')}\n"
            f"{get_localized_text('docs.item_standard')}\n"
            f"{get_localized_text('docs.item_pay')}\n"
            f"{get_localized_text('docs.item_help')}\n\n"
            f"{get_localized_text('docs.reply_footer')}"
        )

        if callback.message and hasattr(callback.message, "edit_text"):
            await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при возврате к списку документов: {e}", exc_info=True)
        await callback.answer("⚠️ Произошла ошибка", show_alert=True)


@router.message(Command("news"))
async def show_news(message: Message) -> None:
    """Показать новости"""
    try:
        user = await get_user(message.from_user.id)

        # Проверяем доступ к новостям
        if not user:
            await message.answer("❌ Для доступа к новостям необходимо войти в систему")
            return

        # Получаем новости с улучшенным парсером согласно Context7
        news_cards = await get_news_cards(limit=5)

        if not news_cards:
            await message.answer("📰 Новости временно недоступны. Попробуйте позже.")
            return

        # Отправляем каждую новость отдельным сообщением
        for i, item in enumerate(news_cards, 1):
            text = (
                f"{get_localized_text('news.card_header', title=item['title'])}\n"
                f"{get_localized_text('news.card_date', date=item['date'])}\n"
                f"{get_localized_text('news.card_desc', desc=item['desc'])}"
            )

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=get_localized_text("news.card_more"), url=item["url"]
                        )
                    ]
                ]
            )

            await message.answer(text, reply_markup=kb)

        # Добавляем информацию о количестве новостей
        await message.answer(f"📰 Показано {len(news_cards)} последних новостей")

    except Exception as e:
        logger.error(f"Ошибка при показе новостей: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при загрузке новостей")


@router.message(Command("announce"))
async def admin_announce(message: Message) -> None:
    """Административное объявление (только для админов и директоров)"""
    try:
        user = await get_user(message.from_user.id)

        # Проверяем права доступа
        if not user or user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
            await message.answer("❌ У вас нет прав для отправки объявлений")
            return

        # Парсим команду: /announce текст_объявления
        if message.text is None:
            await message.answer("Использование: /announce текст_объявления")
            return

        announcement_text = message.text.replace("/announce", "").strip()
        if not announcement_text:
            await message.answer("Использование: /announce текст_объявления")
            return

        # Формируем официальное сообщение с улучшенной локализацией согласно Context7
        url = "https://www.mos.ru/donm/"
        msg = get_localized_text("admin.announcement", announcement=announcement_text, url=url)

        # Здесь должна быть логика рассылки всем пользователям
        # Пока просто отправляем в чат
        await message.answer(f"📢 **ОФИЦИАЛЬНОЕ ОБЪЯВЛЕНИЕ**\n\n{msg}", parse_mode="HTML")

        await message.answer("✅ Объявление отправлено")

    except Exception as e:
        logger.error(f"Ошибка при отправке объявления: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при отправке объявления")


def get_recipients(role: str = "all") -> List[int]:
    """Получить список получателей для рассылки"""
    # TODO: Реализовать получение списка пользователей из БД
    # Пока возвращаем заглушку
    return [123456, 7891011]  # Пример user_id
