"""Testes de resiliência HTTP para agrobr.usda.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.usda import client
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
    make_sleep_tracker,
)


class TestUsdaApiKey:
    def test_missing_api_key_raises(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(SourceUnavailableError, match="API key não configurada"),
        ):
            client._get_api_key(None)

    def test_explicit_api_key_used(self):
        key = client._get_api_key("my-key")
        assert key == "my-key"

    def test_env_var_api_key_used(self):
        with patch.dict("os.environ", {"AGROBR_USDA_API_KEY": "env-key"}):
            key = client._get_api_key(None)
            assert key == "env-key"


class TestUsdaTimeout:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_json("https://test.usda.gov/api", "key123")

        assert mock_client.get.call_count == 3


class TestUsdaHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_401_raises_immediately(self):
        resp_401 = make_mock_response(401, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_401)

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="API key inválida"),
        ):
            await client._fetch_json("https://test.usda.gov/api", "bad-key")

        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_http_404_returns_empty_list(self):
        resp_404 = make_mock_response(404, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_404)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._fetch_json("https://test.usda.gov/api", "key")

        assert result == []

    @pytest.mark.asyncio
    async def test_http_500_retries(self):
        resp_500 = make_mock_response(500, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_json("https://test.usda.gov/api", "key")

        assert mock_client.get.call_count > 1

    @pytest.mark.asyncio
    async def test_http_429_retries_then_succeeds(self):
        resp_429 = make_mock_response(429, json_data=[])
        resp_ok = make_mock_response(200, json_data=[{"id": 1}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_ok])

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._fetch_json("https://test.usda.gov/api", "key")

        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_http_403_raises_via_raise_for_status(self):
        resp_403 = make_mock_response(403, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._fetch_json("https://test.usda.gov/api", "key")


class TestUsdaEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_list_response(self):
        resp = make_mock_response(200, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._fetch_json("https://test.usda.gov/api", "key")

        assert result == []

    @pytest.mark.asyncio
    async def test_non_list_response_returns_empty(self):
        resp = make_mock_response(200, json_data={"error": "unexpected"})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._fetch_json("https://test.usda.gov/api", "key")

        assert result == []


class TestUsdaRetryBackoff:
    @pytest.mark.asyncio
    async def test_backoff_exponential(self):
        resp_500 = make_mock_response(500, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        sleep_calls, track_sleep = make_sleep_tracker()

        with (
            patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, side_effect=track_sleep),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_json("https://test.usda.gov/api", "key")

        assert len(sleep_calls) >= 2
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] > sleep_calls[i - 1]


class TestPsdWrappers:
    @pytest.mark.asyncio
    async def test_fetch_psd_country(self):
        resp_ok = make_mock_response(200, json_data=[{"commodity": "Soybeans"}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_ok)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_psd_country("2222000", "BR", 2025, api_key="test-key")

        assert result == [{"commodity": "Soybeans"}]
        called_url = mock_client.get.call_args[0][0]
        assert "/psd/commodity/2222000/country/BR/year/2025" in called_url

    @pytest.mark.asyncio
    async def test_fetch_psd_world(self):
        resp_ok = make_mock_response(200, json_data=[{"world": True}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_ok)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_psd_world("2222000", 2025, api_key="test-key")

        assert result == [{"world": True}]
        called_url = mock_client.get.call_args[0][0]
        assert "/psd/commodity/2222000/world/year/2025" in called_url

    @pytest.mark.asyncio
    async def test_fetch_psd_all_countries(self):
        resp_ok = make_mock_response(200, json_data=[{"all": True}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_ok)

        with patch("agrobr.usda.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_psd_all_countries("2222000", 2025, api_key="test-key")

        assert result == [{"all": True}]
        called_url = mock_client.get.call_args[0][0]
        assert "/psd/commodity/2222000/country/all/year/2025" in called_url
