# app/bot.py
import asyncio
import logging.config
import pathlib
import signal
from datetime import date, timedelta

import redis.asyncio as redis
import yaml
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message
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
from app.utils.hash import check_pwd

# Configure logging
logging.config.dictConfig(yaml.safe_load(pathlib.Path("logging.yml").read_text()))

# Sentry integration
import sentry_sdk
from aiohttp import web
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def _should_suppress_event(event, hint):
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
        before_send=lambda event, hint: None if _should_suppress_event(event, hint) else event,
    )

bot = Bot(settings.TELEGRAM_TOKEN)
storage = RedisStorage(redis.from_url(settings.REDIS_URL, decode_responses=True))
dp = Dispatcher(storage=storage)


# ────────────────── DB bootstrap ──────────────────
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if not (await conn.execute(select(User))).first():
            await conn.execute(User.__table__.insert(), DEMO_USERS)
            await conn.commit()
        await seed_demo(conn)


async def seed_demo(conn):
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
    student2 = 23  # student02 (5 учителей + 5 админов + 5 директоров = 15; student02 = 15 + 2 = 17, но по порядку вставки = 23)
    student3 = 24  # student03

    # --- заметки учителей ---
    notes = [
        Note(teacher_id=teacher1, student_name="Петров Илья", text="Отличный ответ на уроке"),
        Note(teacher_id=teacher1, student_name="Сидорова Анна", text="Не сдала домашнюю работу"),
        Note(teacher_id=teacher2, student_name="Ким Даниил", text="Помог однокласснику с задачей"),
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
            from_id=student3, text="Ругался с родителями, чувствую стресс", status=Status.open
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
            message="Уважаемые коллеги! Напоминаем о собрании учителей сегодня в 15:00 в актовом зале. Повестка: подготовка к родительским собраниям.",
            target_role="teacher",
            status="delivered",
        ),
    ]

    # Use session for adding objects
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session.add_all(notes + tickets + media + psych + tasks + broadcasts)
        await session.commit()


async def get_user(tg_id: int) -> User | None:
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


async def authenticate(tg_id: int, login: str, pwd: str) -> User | None:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.login == login))
        if user and check_pwd(pwd, user.password) and not user.used:
            await s.execute(update(User).where(User.id == user.id).values(tg_id=tg_id, used=True))
            await s.commit()
            return user
    return None


# ────────────────── /start & логин FSM ──────────────────
@dp.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext, lang: str):
    if await get_user(m.from_user.id):
        u = await get_user(m.from_user.id)
        await m.answer(
            f"Вы уже авторизованы как <b>{ROLES[u.role]}</b>",
            reply_markup=menu(u.role, lang, u.theme),
        )
    else:
        await state.set_state("await_login")
        await m.answer(t("common.start_welcome", lang))


@dp.message(F.text)
async def fsm_login(m: Message, state: FSMContext, lang: str):
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == "await_login":
        data["login"] = m.text.strip()
        await state.set_state("await_pwd")
        await state.set_data(data)
        await m.answer(t("common.login_prompt", lang))
    elif current_state == "await_pwd":
        user = await authenticate(m.from_user.id, data["login"], m.text.strip())
        await state.clear()
        if user:
            nonce = await issue_nonce(dp.storage, m.chat.id, m.from_user.id)
            await m.answer(
                t("common.auth_success", lang),
                reply_markup=menu(user.role, lang, user.theme, nonce),
            )
        else:
            await m.answer(t("common.bad_credentials", lang))
    else:
        await m.answer("Используйте /start для начала.")


# ────────────────── Переключение роли демо-аккаунта ──────────────────
@dp.callback_query(lambda c: c.data.startswith("switch_"))
async def demo_switch(call: CallbackQuery, lang: str):
    role_target = call.data.split("_", 1)[1]  # teacher / admin ...
    user = await get_user(call.from_user.id)
    if not user or user.role != "super":
        await call.answer("Только для демо-аккаунта", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.id == user.id).values(role=role_target))
        await s.commit()
    await call.message.edit_text(
        f"🚀 Вы переключились в режим «{ROLES[role_target]}»",
        reply_markup=menu(role_target, lang, user.theme),
    )
    await call.answer()


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
async def main():
    await init_db()

    # Start health check server
    from app.health import init_health_app

    health_app = await init_health_app()
    runner = web.AppRunner(health_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    # Start KPI metrics loop
    asyncio.create_task(kpi_loop())

    # Graceful shutdown setup
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _sig(*_):
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
