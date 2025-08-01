# app/bot.py
import asyncio
import logging.config
import pathlib
import signal
from datetime import date, timedelta
from typing import Any

import redis.asyncio as redis
import sentry_sdk
import yaml
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import select, update

from app.config import settings
from app.db.base import Base
from app.db.broadcast import Broadcast
from app.db.media_request import MediaRequest
from app.db.note import Note
from app.db.psych_request import PsychRequest
from app.db.session import AsyncSessionLocal, engine
from app.db.task import Task
from app.db.ticket import Ticket
from app.db.user import User
from app.i18n import t
from app.keyboards.main_menu import menu
from app.middlewares.audit import AuditMiddleware
from app.middlewares.csrf import CSRFMiddleware
from app.middlewares.locale import LocaleMiddleware
from app.middlewares.metrics import MetricsMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.sentry_context import SentryContext
from app.middlewares.ux import FallbackMiddleware, UnknownCommandMiddleware
from app.roles import DEMO_USERS, ROLES
from app.routes import include_all
from app.services.scheduler import kpi_loop
from app.utils.csrf import issue_nonce

# Configure logging
logging.config.dictConfig(yaml.safe_load(pathlib.Path("logging.yml").read_text()))

# Sentry integration


def _should_suppress_event(event: Any, hint: Any) -> bool:
    """Filter out validation errors and rate limits from Sentry"""
    exc = hint.get("exc_info", (None, None, None))[1]
    if exc:
        # Suppress validation errors
        if isinstance(exc, ValueError) and "логин" in str(exc).lower():
            return True
        # Suppress rate limit errors
        if "rate" in str(exc).lower() and "limit" in str(exc).lower():
            return True
    return False


# Initialize GlitchTip if DSN is provided
if settings.GLITCHTIP_DSN:
    sentry_sdk.init(
        dsn=settings.GLITCHTIP_DSN,
        integrations=[
            AioHttpIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of performance transactions
        environment=settings.ENV,
        release="schoolbot@1.0.0",
        # Filter out validation errors and rate limits
        before_send=lambda event, hint: (None if _should_suppress_event(event, hint) else event),
    )

bot = Bot(settings.TELEGRAM_TOKEN)
storage = RedisStorage(redis.from_url(settings.REDIS_URL, decode_responses=True))
dp = Dispatcher(storage=storage)


# ────────────────── DB bootstrap ──────────────────
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        result = await conn.execute(select(User))
        if not result.first():
            await conn.execute(User.__table__.insert(), DEMO_USERS)  # type: ignore
            await conn.commit()
        await seed_demo(conn)


async def seed_demo(conn: Any) -> None:
    """
    Наполняем таблицы примерами, если там пусто.
    """
    # Проверяем: есть ли уже записи?
    note_exists = await conn.execute(select(Note.id).limit(1))
    broadcast_exists = await conn.execute(select(Broadcast.id).limit(1))

    # Если есть и заметки, и рассылки - уже засевали
    if note_exists.first() and broadcast_exists.first():
        return  # уже засевали

    # Берём id первых демо-пользователей
    teacher1 = 1  # teacher01
    teacher2 = 2  # teacher02
    student2 = 23  # student02
    student3 = 24  # student03

    # --- заметки учителей ---
    notes = [
        Note(
            teacher_id=teacher1,
            student_name="Петров Илья",
            text="Отличный ответ на уроке",
        ),
        Note(
            teacher_id=teacher1,
            student_name="Сидорова Анна",
            text="Не сдала домашнюю работу",
        ),
        Note(
            teacher_id=teacher2,
            student_name="Ким Даниил",
            text="Помог однокласснику с задачей",
        ),
    ]

    # --- IT-тикеты ---
    from app.db.enums import Status

    tickets = [
        Ticket(author_id=teacher1, title="Не включается проектор", status=Status.open),
        Ticket(author_id=teacher2, title="Не печатает принтер", status=Status.in_progress),
    ]

    # --- медиа-заявка ---
    media = [
        MediaRequest(
            author_id=teacher1,
            event_date=date.today() + timedelta(days=7),
            comment="Съёмка концерта 5-го класса",
            file_id="demo_file_id",  # можно любое строковое значение
            status=Status.open,
        ),
    ]

    # --- обращения к психологу ---
    psych = [
        PsychRequest(
            from_id=student2,
            text="Меня дразнят одноклассники, не хочу идти в школу",
            status=Status.open,
        ),
        PsychRequest(
            from_id=student3,
            text="Ругался с родителями, чувствую стресс",
            status=Status.open,
        ),
    ]

    # --- поручения директора ---
    from app.db.task import TaskStatus

    tasks = [
        Task(
            title="Подготовить отчёт по успеваемости",
            description="Собрать данные по всем классам за текущий месяц",
            status=TaskStatus.PENDING,
            author_id=1,
            assigned_to_id=teacher1,
            deadline=date.today() + timedelta(days=3),
        ),  # author_id=1 (директор)
        Task(
            title="Обновить расписание в МЭШ",
            description="Внести изменения в электронное расписание",
            status=TaskStatus.PENDING,
            author_id=1,
            assigned_to_id=teacher2,
            deadline=date.today() - timedelta(days=1),
        ),  # author_id=1 (директор) - просрочено
    ]

    # --- массовые рассылки админа ---
    broadcasts = [
        Broadcast(
            author_id=6,  # admin01
            title="Собрание учителей",
            message=(
                "Уважаемые коллеги! Напоминаем о собрании учителей сегодня в 15:00 "
                "в актовом зале. Повестка: подготовка к родительским собраниям."
            ),
            target_role="teacher",
            status="delivered",
        ),
    ]

    # Use session for adding objects
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )  # type: ignore

    async with async_session() as session:
        session.add_all(notes + tickets + media + psych + tasks + broadcasts)
        await session.commit()


async def get_user(tg_id: int) -> Any:
    """Получить пользователя по Telegram ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()


async def authenticate(tg_id: int, login: str, pwd: str) -> Any:
    """Аутентификация пользователя"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.login == login, User.password == pwd, User.used.is_(False))
        )
        user = result.scalar_one_or_none()
        if user:
            user.tg_id = tg_id
            user.used = True
            await session.commit()
        return user


# ────────────────── /start & логин FSM ──────────────────
@dp.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext, lang: str) -> None:
    if m.from_user is None:
        await m.answer("Ошибка: пользователь не найден.")
        return

    user = await get_user(m.from_user.id)
    if user:
        await m.answer(
            f"Вы уже авторизованы как <b>{ROLES[str(user.role)]}</b>",
            reply_markup=menu(str(user.role), lang, str(user.theme)),
        )
    else:
        # Предлагаем онбординг для новых пользователей
        welcome_text = (
            "🎓 **Добро пожаловать в SchoolBot!**\n\n"
            "Это образовательная платформа для всех участников учебного процесса.\n\n"
            "Выберите, что хотите сделать:"
        )

        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Пройти онбординг", callback_data="start_onboarding"
                    ),
                    InlineKeyboardButton(text="🔑 Войти в систему", callback_data="start_login"),
                ]
            ]
        )

        await m.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")


@dp.message(F.text)
async def fsm_login(m: Message, state: FSMContext, lang: str) -> None:
    """Обработка логина через FSM"""
    if m.from_user is None:
        await m.answer("Ошибка: пользователь не найден.")
        return

    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == "await_login":
        if m.text is None:
            await m.answer("Пожалуйста, введите логин.")
            return
        data["login"] = m.text.strip()
        await state.set_state("await_pwd")
        await state.set_data(data)
        await m.answer(t("common.login_prompt", lang))
    elif current_state == "await_pwd":
        if m.text is None:
            await m.answer("Пожалуйста, введите пароль.")
            return
        user = await authenticate(m.from_user.id, data["login"], m.text.strip())
        await state.clear()
        if user:
            nonce = await issue_nonce(dp.storage, m.chat.id, m.from_user.id)
            await m.answer(
                t("common.auth_success", lang),
                reply_markup=menu(str(user.role), lang, str(user.theme), nonce),
            )
        else:
            await m.answer(t("common.bad_credentials", lang))
    else:
        await m.answer("Используйте /start для начала.")


# ────────────────── Обработка выбора действия при старте ──────────────────
@dp.callback_query(F.data == "start_onboarding")
async def handle_start_onboarding(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Обработка выбора онбординга"""
    from app.handlers.onboarding import start_onboarding

    await start_onboarding(call.message, state, lang)
    await call.answer()


@dp.callback_query(F.data == "start_login")
async def handle_start_login(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Обработка выбора входа в систему"""
    await state.set_state("await_login")
    if call.message is not None and hasattr(call.message, "edit_text"):
        await call.message.edit_text(t("common.start_welcome", lang))
    await call.answer()


# ────────────────── Переключение роли демо-аккаунта ──────────────────
@dp.callback_query(lambda c: c.data.startswith("switch_"))
async def demo_switch(call: CallbackQuery, lang: str) -> None:
    """Переключение между демо-аккаунтами"""
    if call.from_user is None:
        await call.answer("Ошибка: пользователь не найден.", show_alert=True)
        return

    if call.data is None:
        await call.answer("Ошибка данных", show_alert=True)
        return
    role_target = call.data.split("_", 1)[1]  # teacher / admin ...
    user = await get_user(call.from_user.id)
    if not user or user.role != "super":
        await call.answer("Только для демо-аккаунта", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        if user is not None and hasattr(user, "id") and user.id is not None:
            await s.execute(update(User).where(User.id == user.id).values(role=role_target))
            await s.commit()
    if call.message is not None and hasattr(call.message, "edit_text"):
        await call.message.edit_text(
            f"🚀 Вы переключились в режим «{ROLES[role_target]}»",
            reply_markup=menu(role_target, lang, user.theme),
        )
        await call.answer()
    else:
        await call.answer()
        return
    return


# ────────────────── Подключение роутеров ──────────────────
include_all(dp)

# ────────────────── Middleware ──────────────────
dp.message.middleware(LocaleMiddleware())
dp.callback_query.middleware(LocaleMiddleware())
dp.message.middleware(MetricsMiddleware())
dp.callback_query.middleware(MetricsMiddleware())
dp.message.middleware(UnknownCommandMiddleware())
dp.message.middleware(FallbackMiddleware())
dp.message.middleware(RateLimitMiddleware())
dp.callback_query.middleware(CSRFMiddleware())
dp.update.middleware(SentryContext())
dp.update.middleware(AuditMiddleware())


# ────────────────── Запуск ──────────────────
async def main() -> None:
    """Главная функция"""
    await init_db()

    # Start health check server
    from aiohttp import web

    from app.health import init_health_app

    health_app = await init_health_app()
    runner = web.AppRunner(health_app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8080)
    await site.start()

    # Start KPI metrics loop
    asyncio.create_task(kpi_loop())

    # Graceful shutdown setup
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _sig(*_: Any) -> None:
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _sig)

    # Start bot polling
    polling = asyncio.create_task(dp.start_polling(bot, skip_updates=True))
    await stop.wait()
    polling.cancel()
    await bot.session.close()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
