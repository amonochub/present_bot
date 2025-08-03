#!/usr/bin/env python3
import asyncio
import logging
import sys

from app.bot import main

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("bot.log")],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting School Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
