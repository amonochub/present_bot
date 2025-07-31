"""
Health check endpoint for monitoring
"""

import asyncio

import sentry_sdk
from aiohttp import web
from prometheus_client import generate_latest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User


async def health_check(request):
    """Health check endpoint"""
    try:
        # Check database connection
        async with AsyncSessionLocal() as session:
            await session.execute(select(User).limit(1))
            await session.commit()

        # Check Redis connection (if needed)
        # redis_client = redis.from_url(REDIS_URL)
        # await redis_client.ping()

        return web.json_response(
            {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "database": "connected",
                "redis": "connected",
            }
        )
    except Exception as e:
        # Report to Sentry if available
        if sentry_sdk.Hub.current:
            sentry_sdk.capture_exception(e)

        return web.json_response(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            },
            status=500,
        )


async def init_health_app():
    """Initialize health check app"""
    app = web.Application()
    app.router.add_get("/healthz", health_check)
    app.router.add_get("/", health_check)  # Root endpoint
    app.router.add_get("/metrics", metrics)  # Prometheus metrics
    return app


async def metrics(request):
    """Prometheus metrics endpoint"""
    return web.Response(body=generate_latest(), content_type="text/plain; version=0.0.4")
