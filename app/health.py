"""
Health check endpoint for monitoring
"""

import asyncio
import os
import time
from typing import Dict, Any

import redis.asyncio as redis
import sentry_sdk
from aiohttp import web
from prometheus_client import generate_latest
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.db.user import User


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint"""
    start_time = time.time()
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": start_time,
        "version": "1.0.0",
        "environment": settings.ENV,
    }

    try:
        # Check database connection
        db_start = time.time()
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(select(User).limit(1))
                await session.commit()
            db_time = time.time() - db_start

            health_data["database"] = {
                "status": "connected",
                "response_time": round(db_time * 1000, 2),  # ms
            }
        except Exception as db_error:
            health_data["database"] = {
                "status": "error",
                "error": str(db_error),
                "response_time": None,
            }

        # Check Redis connection
        redis_start = time.time()
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            await redis_client.ping()
            redis_time = time.time() - redis_start

            health_data["redis"] = {
                "status": "connected",
                "response_time": round(redis_time * 1000, 2),  # ms
            }

            await redis_client.close()
        except Exception as redis_error:
            health_data["redis"] = {
                "status": "error",
                "error": str(redis_error),
                "response_time": None,
            }

        # Check environment variables
        health_data["environment_vars"] = {
            "telegram_token_set": bool(settings.TELEGRAM_TOKEN),
            "database_configured": bool(settings.DB_NAME and settings.DB_USER),
            "redis_configured": bool(settings.REDIS_DSN),
            "sentry_configured": bool(settings.GLITCHTIP_DSN),
        }

        # Check system resources
        try:
            import psutil

            health_data["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except ImportError:
            health_data["system"] = {"error": "psutil not available"}

        # Calculate total response time
        total_time = time.time() - start_time
        health_data["response_time"] = round(total_time * 1000, 2)  # ms

        return web.json_response(health_data)

    except Exception as e:
        # Report to Sentry if available
        if sentry_sdk.Hub.current:
            sentry_sdk.capture_exception(e)

        health_data.update(
            {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )

        return web.json_response(health_data, status=500)


async def detailed_health_check(request: web.Request) -> web.Response:
    """Detailed health check with more information"""
    try:
        health_response = await health_check(request)

        # Add additional information for detailed check
        if hasattr(health_response, "body"):
            import json

            health_data = json.loads(health_response.body.decode())

            health_data["detailed"] = {
                "process_id": os.getpid(),
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "ENV": settings.ENV,
                    "DB_HOST": settings.DB_HOST,
                    "DB_PORT": settings.DB_PORT,
                    "DB_NAME": settings.DB_NAME,
                    "REDIS_DSN": (
                        settings.REDIS_DSN[:20] + "..."
                        if len(settings.REDIS_DSN) > 20
                        else settings.REDIS_DSN
                    ),
                },
            }

            return web.json_response(
                health_data, status=health_response.status
            )
        else:
            return health_response

    except Exception as e:
        return web.json_response(
            {
                "status": "error",
                "error": f"Failed to get detailed health check: {str(e)}",
                "timestamp": time.time(),
            },
            status=500,
        )


async def init_health_app() -> web.Application:
    """Initialize health check app"""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/healthz", health_check)  # Alias for compatibility
    app.router.add_get("/health/detailed", detailed_health_check)
    app.router.add_get("/", health_check)  # Root endpoint
    app.router.add_get("/metrics", metrics)  # Prometheus metrics
    return app


async def metrics(request: web.Request) -> web.Response:
    """Prometheus metrics endpoint"""
    try:
        return web.Response(
            body=generate_latest(), content_type="text/plain; version=0.0.4"
        )
    except Exception as e:
        return web.json_response(
            {
                "error": f"Failed to generate metrics: {str(e)}",
                "timestamp": time.time(),
            },
            status=500,
        )
