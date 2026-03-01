"""Testes de resiliência HTTP para agrobr.anda.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.anda import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import make_mock_async_client, make_mock_response

RETRY_SLEEP = "agrobr.http.retry.asyncio.sleep"


class TestAndaTimeout:
    @pytest.mark.asyncio
    async def test_timeout_propagates_immediately(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.TimeoutException),
        ):
            await client._get_with_retry("https://anda.org.br/test")

        assert mock_client.get.call_count == 1


class TestAndaHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_500_retries_then_succeeds(self):
        resp_500 = make_mock_response(
            500, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        resp_ok = make_mock_response(
            200, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_500, resp_500, resp_ok])

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._get_with_retry("https://anda.org.br/test")

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_http_403_raises_via_raise_for_status(self):
        resp_403 = make_mock_response(
            403, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._get_with_retry("https://anda.org.br/test")

        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_http_404_raises_via_raise_for_status(self):
        resp_404 = make_mock_response(
            404, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_404)

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._get_with_retry("https://anda.org.br/test")

        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_http_429_retries(self):
        resp_429 = make_mock_response(
            429, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        resp_ok = make_mock_response(
            200, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_ok])

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._get_with_retry("https://anda.org.br/test")

        assert result.status_code == 200


class TestAndaConnectError:
    @pytest.mark.asyncio
    async def test_connect_error_propagates_immediately(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.ConnectError("refused")

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.ConnectError),
        ):
            await client._get_with_retry("https://anda.org.br/test")

        assert mock_client.get.call_count == 1


class TestAndaEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_html_raises_source_unavailable(self):
        resp = make_mock_response(200, text="", content=b"data", url="https://anda.org.br/test")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await client.fetch_estatisticas_page()

    def test_parse_links_empty_html(self):
        links = client.parse_links_from_html("")
        assert links == []

    def test_parse_links_malformed_html(self):
        links = client.parse_links_from_html("<html><broken><<<")
        assert links == []


class TestAndaRetryBackoff:
    @pytest.mark.asyncio
    async def test_backoff_exponential(self):
        resp_500 = make_mock_response(
            500, text="<html></html>", content=b"data", url="https://anda.org.br/test"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        sleep_calls: list[float] = []

        async def track_sleep(delay: float) -> None:
            sleep_calls.append(delay)

        with (
            patch("agrobr.anda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, side_effect=track_sleep),
            pytest.raises(SourceUnavailableError),
        ):
            await client._get_with_retry("https://anda.org.br/test")

        assert len(sleep_calls) >= 2
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] > sleep_calls[i - 1]


class TestFetchEntregasPdf:
    @pytest.mark.asyncio
    async def test_no_pdf_found_raises(self):
        with (
            patch(
                "agrobr.anda.client.fetch_estatisticas_page", new_callable=AsyncMock
            ) as mock_page,
            pytest.raises(FileNotFoundError, match="não encontrado"),
        ):
            mock_page.return_value = "<html><body>no links</body></html>"
            await client.fetch_entregas_pdf(2024)
