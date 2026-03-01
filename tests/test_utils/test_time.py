from __future__ import annotations

from datetime import UTC, datetime

from agrobr.utils.time import utcnow


def test_utcnow_returns_naive():
    assert utcnow().tzinfo is None


def test_utcnow_close_to_utc():
    aware = datetime.now(UTC)
    naive = utcnow()
    assert abs((aware.replace(tzinfo=None) - naive).total_seconds()) < 1
