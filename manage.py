#!/usr/bin/env python3
import asyncio
import subprocess

import typer

from alembic.config import main as alembic_main
from app.bot import seed_demo
from app.db.session import engine

cli = typer.Typer(help="Утилита админа SchoolBot")


@cli.command()
def migrate():
    """alembic upgrade head"""
    alembic_main(["upgrade", "head"])


@cli.command()
def makemigrations(msg: str = "auto"):
    """Создать миграцию"""
    alembic_main(["revision", "--autogenerate", "-m", msg])


@cli.command()
def seed():
    """Заполнить демо-данными (safe)"""

    async def _seed():
        async with engine.begin() as conn:
            await seed_demo(conn)

    asyncio.run(_seed())


@cli.command()
def backup():
    """Ручной бэкап (использует scripts/backup.sh)"""
    subprocess.run(["./scripts/backup.sh"], check=True)


@cli.command()
def shell():
    """Запустить Python shell с подключением к БД"""
    import code

    from app.db.session import engine

    async def _shell():
        async with engine.begin() as conn:
            # Создаем локальные переменные для shell
            locals_dict = {
                "engine": engine,
                "conn": conn,
                "Base": Base,
            }
            # Импортируем модели
            from app.db import broadcast, media_request, note, psych_request, ticket, user

            locals_dict.update(
                {
                    "User": user.User,
                    "Ticket": ticket.Ticket,
                    "Note": note.Note,
                    "MediaRequest": media_request.MediaRequest,
                    "PsychRequest": psych_request.PsychRequest,
                    "Broadcast": broadcast.Broadcast,
                }
            )
            code.interact(local=locals_dict)

    asyncio.run(_shell())


if __name__ == "__main__":
    cli()
