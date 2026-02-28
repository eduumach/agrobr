from __future__ import annotations

import asyncio
import time
from asyncio import sleep as _async_sleep
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog

from agrobr import constants

logger = structlog.get_logger()


class RateLimiter:
    _semaphores: dict[str, asyncio.Semaphore] = {}
    _last_request: dict[str, float] = {}
    _lock: asyncio.Lock | None = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    def _get_delay(cls, source_key: str) -> float:
        settings = constants.HTTPSettings()
        return getattr(settings, f"rate_limit_{source_key}", settings.rate_limit_default)

    @classmethod
    @asynccontextmanager
    async def acquire(cls, source: constants.Fonte | str) -> AsyncIterator[None]:
        source_key = source.value if isinstance(source, constants.Fonte) else source

        async with cls._get_lock():
            if source_key not in cls._semaphores:
                cls._semaphores[source_key] = asyncio.Semaphore(1)

        async with cls._semaphores[source_key]:
            now = time.monotonic()
            last = cls._last_request.get(source_key, 0)
            delay = cls._get_delay(source_key)
            elapsed = now - last

            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(
                    "rate_limit_wait",
                    source=source_key,
                    wait_seconds=wait_time,
                )
                await _async_sleep(wait_time)

            try:
                yield
            finally:
                cls._last_request[source_key] = time.monotonic()

    @classmethod
    def reset(cls) -> None:
        cls._semaphores.clear()
        cls._last_request.clear()
        cls._lock = None
