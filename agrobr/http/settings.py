from __future__ import annotations

import httpx

from agrobr.constants import HTTPSettings


def get_timeout(
    settings: HTTPSettings | None = None,
    *,
    read: float | None = None,
) -> httpx.Timeout:
    s = settings or HTTPSettings()
    return httpx.Timeout(
        connect=s.timeout_connect,
        read=read if read is not None else s.timeout_read,
        write=s.timeout_write,
        pool=s.timeout_pool,
    )
