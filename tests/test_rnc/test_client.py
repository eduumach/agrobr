from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from agrobr.exceptions import SourceUnavailableError


@pytest.mark.asyncio
async def test_fetch_registradas_returns_csv_bytes():
    fake_search = MagicMock(spec=httpx.Response)
    fake_search.status_code = 200
    fake_search.content = b"<html>search results</html>"
    fake_search.raise_for_status = MagicMock()

    fake_csv = MagicMock(spec=httpx.Response)
    fake_csv.status_code = 200
    fake_csv.content = b"A" * 600_000
    fake_csv.raise_for_status = MagicMock()

    with patch("agrobr.rnc.client.retry_on_status", new_callable=AsyncMock) as mock_retry:
        mock_retry.side_effect = [fake_search, fake_csv]

        from agrobr.rnc.client import fetch_registradas

        content, url = await fetch_registradas()
        assert len(content) == 600_000
        assert "cultivares_registradas" in url
        assert mock_retry.call_count == 2


@pytest.mark.asyncio
async def test_fetch_raises_on_small_csv():
    fake_search = MagicMock(spec=httpx.Response)
    fake_search.status_code = 200
    fake_search.content = b"<html></html>"
    fake_search.raise_for_status = MagicMock()

    fake_csv = MagicMock(spec=httpx.Response)
    fake_csv.status_code = 200
    fake_csv.content = b"tiny"
    fake_csv.raise_for_status = MagicMock()

    with patch("agrobr.rnc.client.retry_on_status", new_callable=AsyncMock) as mock_retry:
        mock_retry.side_effect = [fake_search, fake_csv]

        from agrobr.rnc.client import fetch_registradas

        with pytest.raises(SourceUnavailableError):
            await fetch_registradas()


@pytest.mark.asyncio
async def test_fetch_protegidas_returns_csv_bytes():
    fake_search = MagicMock(spec=httpx.Response)
    fake_search.status_code = 200
    fake_search.content = b"<html>search results</html>"
    fake_search.raise_for_status = MagicMock()

    fake_csv = MagicMock(spec=httpx.Response)
    fake_csv.status_code = 200
    fake_csv.content = b"B" * 600_000
    fake_csv.raise_for_status = MagicMock()

    with patch("agrobr.rnc.client.retry_on_status", new_callable=AsyncMock) as mock_retry:
        mock_retry.side_effect = [fake_search, fake_csv]

        from agrobr.rnc.client import fetch_protegidas

        content, url = await fetch_protegidas()
        assert len(content) == 600_000
        assert "cultivares_protegidas" in url
