from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.bcb import ptax_client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
)

GOLDEN = Path(__file__).resolve().parent.parent / "golden_data" / "bcb" / "ptax_sample.json"
SAMPLE = json.loads(GOLDEN.read_text(encoding="utf-8"))


class TestUrlConstruction:
    @pytest.mark.asyncio
    async def test_single_day_uses_dia_endpoint(self):
        resp = make_mock_response(200, json_data=SAMPLE)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client):
            _, url = await ptax_client.fetch_ptax(data="02/01/2026")

        assert "CotacaoDolarDia" in url
        assert "01-02-2026" in url

    @pytest.mark.asyncio
    async def test_period_uses_periodo_endpoint(self):
        resp = make_mock_response(200, json_data=SAMPLE)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client):
            _, url = await ptax_client.fetch_ptax(
                data_inicial="02/01/2026", data_final="08/01/2026"
            )

        assert "CotacaoDolarPeriodo" in url
        assert "01-02-2026" in url
        assert "01-08-2026" in url

    @pytest.mark.asyncio
    async def test_no_args_defaults_to_last_30_days(self):
        resp = make_mock_response(200, json_data=SAMPLE)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client):
            _, url = await ptax_client.fetch_ptax()

        assert "CotacaoDolarPeriodo" in url


class TestDateConversion:
    def test_brazilian_to_api_format(self):
        assert ptax_client._to_api_date("15/03/2026") == "03-15-2026"

    def test_single_digit_day_month(self):
        assert ptax_client._to_api_date("01/01/2026") == "01-01-2026"

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            ptax_client._to_api_date("invalid-date")


class TestEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_value_list(self):
        resp = make_mock_response(200, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client):
            records, _ = await ptax_client.fetch_ptax(data="01/01/2026")

        assert records == []

    @pytest.mark.asyncio
    async def test_missing_value_key(self):
        resp = make_mock_response(200, json_data={"@odata.context": "..."})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client):
            records, _ = await ptax_client.fetch_ptax(data="01/01/2026")

        assert records == []


class TestRetry:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await ptax_client.fetch_ptax(data="02/01/2026")

        assert mock_client.get.call_count == ptax_client.PTAX_MAX_RETRIES

    @pytest.mark.asyncio
    async def test_http_500_retries_then_recovers(self):
        resp_500 = make_mock_response(500, json_data={"value": []})
        resp_ok = make_mock_response(200, json_data=SAMPLE)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_500, resp_ok])

        with (
            patch("agrobr.bcb.ptax_client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            records, _ = await ptax_client.fetch_ptax(data="02/01/2026")

        assert len(records) == 5
