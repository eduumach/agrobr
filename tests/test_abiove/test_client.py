"""Testes de resiliência HTTP para agrobr.abiove.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.abiove import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
    make_sleep_tracker,
)


class TestAbioveTimeout:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("connect timeout")

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert mock_client.get.call_count == 3


class TestAbioveHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_500_retries_then_fails(self):
        resp_500 = make_mock_response(
            500, content=b"xlsx-data", url="https://abiove.org.br/test.xlsx"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert mock_client.get.call_count > 1

    @pytest.mark.asyncio
    async def test_http_404_raises_immediately(self):
        resp_404 = make_mock_response(
            404, content=b"xlsx-data", url="https://abiove.org.br/test.xlsx"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_404)

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="HTTP 404"),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_http_403_raises_via_raise_for_status(self):
        resp_403 = make_mock_response(
            403, content=b"xlsx-data", url="https://abiove.org.br/test.xlsx"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

    @pytest.mark.asyncio
    async def test_http_429_retries(self):
        resp_429 = make_mock_response(
            429, content=b"xlsx-data", url="https://abiove.org.br/test.xlsx"
        )
        ok_content = b"x" * 1500
        resp_ok = make_mock_response(200, content=ok_content, url="https://abiove.org.br/test.xlsx")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_429, resp_ok])

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert result == ok_content


class TestAbioveEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_body_raises_source_unavailable(self):
        resp = make_mock_response(200, content=b"", url="https://abiove.org.br/test.xlsx")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")


class TestAbioveRetry:
    @pytest.mark.asyncio
    async def test_retry_backoff_exponential(self):
        resp_500 = make_mock_response(
            500, content=b"xlsx-data", url="https://abiove.org.br/test.xlsx"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        sleep_calls, track_sleep = make_sleep_tracker()

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, side_effect=track_sleep),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert len(sleep_calls) >= 2
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] > sleep_calls[i - 1]


class TestAbioveConnectError:
    @pytest.mark.asyncio
    async def test_connect_error_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.ConnectError("connection refused")

        with (
            patch("agrobr.abiove.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_url("https://abiove.org.br/test.xlsx")

        assert mock_client.get.call_count == 3


class TestFetchExportacaoExcel:
    @pytest.mark.asyncio
    async def test_specific_month_404_raises(self):
        with (
            patch("agrobr.abiove.client._fetch_url", new_callable=AsyncMock) as mock_fetch,
            pytest.raises(SourceUnavailableError),
        ):
            mock_fetch.side_effect = SourceUnavailableError(
                source="abiove", url="test", last_error="HTTP 404"
            )
            await client.fetch_exportacao_excel(2024, mes=6)

    @pytest.mark.asyncio
    async def test_scans_months_backwards(self):
        with patch("agrobr.abiove.client._fetch_url", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                SourceUnavailableError(source="abiove", url="t", last_error="404"),
                SourceUnavailableError(source="abiove", url="t", last_error="404"),
                b"found",
            ]
            data, url = await client.fetch_exportacao_excel(2024)
            assert data == b"found"
            assert mock_fetch.call_count == 3
