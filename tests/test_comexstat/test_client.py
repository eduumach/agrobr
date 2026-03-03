"""Testes de resiliência HTTP para agrobr.comexstat.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.comexstat import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
    make_sleep_tracker,
)


class TestComexstatTimeout:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client.download_csv("https://test.gov.br/EXP_2024.csv")

        assert mock_client.get.call_count == 3


class TestComexstatHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_500_retries_then_fails(self):
        resp_500 = make_mock_response(
            500, text="col1;col2\nval1;val2", url="https://test.gov.br/EXP_2024.csv"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client.download_csv("https://test.gov.br/EXP_2024.csv")

        assert mock_client.get.call_count > 1

    @pytest.mark.asyncio
    async def test_http_403_raises_via_raise_for_status(self):
        resp_403 = make_mock_response(
            403, text="col1;col2\nval1;val2", url="https://test.gov.br/EXP_2024.csv"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client.download_csv("https://test.gov.br/EXP_2024.csv")

    @pytest.mark.asyncio
    async def test_http_429_retries_then_succeeds(self):
        ok_text = (
            "CO_ANO;CO_MES;CO_NCM;CO_PAIS;SG_UF;KG_LIQUIDO;VL_FOB\n"
            + "2024;01;12019010;160;SP;1000;5000\n" * 5
        )
        resp_429 = make_mock_response(
            429, text="col1;col2\nval1;val2", url="https://test.gov.br/EXP_2024.csv"
        )
        resp_ok = make_mock_response(200, text=ok_text, url="https://test.gov.br/EXP_2024.csv")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_429, resp_ok])

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client.download_csv("https://test.gov.br/EXP_2024.csv")

        assert result == ok_text


class TestComexstatEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_body_raises_source_unavailable(self):
        resp = make_mock_response(200, text="", url="https://test.gov.br/EXP_2024.csv")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await client.download_csv("https://test.gov.br/EXP_2024.csv")


class TestComexstatRetryBackoff:
    @pytest.mark.asyncio
    async def test_backoff_exponential(self):
        resp_500 = make_mock_response(
            500, text="col1;col2\nval1;val2", url="https://test.gov.br/EXP_2024.csv"
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        sleep_calls, track_sleep = make_sleep_tracker()

        with (
            patch("agrobr.comexstat.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, side_effect=track_sleep),
            pytest.raises(SourceUnavailableError),
        ):
            await client.download_csv("https://test.gov.br/EXP_2024.csv")

        assert len(sleep_calls) >= 2
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] > sleep_calls[i - 1]


class TestComexstatFetchHelpers:
    @pytest.mark.asyncio
    async def test_fetch_exportacao_builds_correct_url(self):
        with patch("agrobr.comexstat.client.download_csv", new_callable=AsyncMock) as mock:
            mock.return_value = "data"
            await client.fetch_exportacao_csv(2024)
            mock.assert_called_once()
            url_arg = mock.call_args[0][0]
            assert "EXP_2024.csv" in url_arg

    @pytest.mark.asyncio
    async def test_fetch_importacao_builds_correct_url(self):
        with patch("agrobr.comexstat.client.download_csv", new_callable=AsyncMock) as mock:
            mock.return_value = "data"
            await client.fetch_importacao_csv(2024)
            url_arg = mock.call_args[0][0]
            assert "IMP_2024.csv" in url_arg
