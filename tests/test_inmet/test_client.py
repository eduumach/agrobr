"""Testes de resiliência HTTP para agrobr.inmet.client."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.inmet import client
from tests.helpers import make_mock_async_client, make_mock_response


class TestInmetTimeout:
    @pytest.mark.asyncio
    async def test_timeout_on_get_json(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        with (
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.TimeoutException),
        ):
            await client._get_json("/estacoes/T")

    @pytest.mark.asyncio
    async def test_timeout_on_fetch_estacoes(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        with (
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.TimeoutException),
        ):
            await client.fetch_estacoes("T")


class TestInmetHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_500_raises(self):
        resp_500 = make_mock_response(500, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="inmet"),
        ):
            await client._get_json("/estacoes/T")

    @pytest.mark.asyncio
    async def test_http_403_raises(self):
        resp_403 = make_mock_response(403, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._get_json("/estacoes/T")

    @pytest.mark.asyncio
    async def test_http_429_raises_after_retries(self):
        resp_429 = make_mock_response(429, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_429)

        with (
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="inmet"),
        ):
            await client._get_json("/estacoes/T")

    @pytest.mark.asyncio
    async def test_retriable_status_in_fetch_dados_logged_and_skipped(self):
        resp_ok = make_mock_response(200, json_data=[{"data": "d1"}])
        resp_502 = make_mock_response(502, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_502, resp_ok])

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_dados_estacao("A001", date(2024, 1, 1), date(2024, 1, 2))

        assert isinstance(result, list)


class TestInmetHTTP204:
    @pytest.mark.asyncio
    async def test_204_returns_empty_list(self):
        resp_204 = make_mock_response(204)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_204)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._get_json("/estacao/A001/2024-01-01/2024-01-10")

        assert result == []

    @pytest.mark.asyncio
    async def test_204_in_fetch_dados_returns_empty(self):
        resp_204 = make_mock_response(204)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_204)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_dados_estacao("A001", date(2024, 1, 1), date(2024, 1, 10))

        assert result == []


class TestInmetToken:
    def test_get_token_returns_env_var(self):
        with patch.dict("os.environ", {"AGROBR_INMET_TOKEN": "my-secret-token"}):
            assert client._get_token() == "my-secret-token"

    def test_get_token_returns_none_when_absent(self):
        with patch.dict("os.environ", {}, clear=True):
            result = client._get_token()
            assert result is None

    def test_build_headers_with_token(self):
        with patch.dict("os.environ", {"AGROBR_INMET_TOKEN": "my-secret-token"}):
            headers = client._build_headers()
            assert headers["Authorization"] == "Bearer my-secret-token"
            assert "User-Agent" in headers

    def test_build_headers_without_token(self):
        with patch.dict("os.environ", {}, clear=True):
            headers = client._build_headers()
            assert "Authorization" not in headers
            assert "User-Agent" in headers

    @pytest.mark.asyncio
    async def test_token_sent_in_request_headers(self):
        resp = make_mock_response(200, json_data=[{"data": "d1"}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch.dict("os.environ", {"AGROBR_INMET_TOKEN": "test-token"}),
            patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client) as mock_cls,
        ):
            await client._get_json("/estacoes/T")

        call_kwargs = mock_cls.call_args
        headers_used = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers_used.get("Authorization") == "Bearer test-token"


class TestInmetEndpointPath:
    @pytest.mark.asyncio
    async def test_fetch_dados_uses_new_path(self):
        resp = make_mock_response(200, json_data=[{"data": "d1"}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            await client.fetch_dados_estacao("A001", date(2024, 1, 1), date(2024, 1, 10))

        call_url = mock_client.get.call_args[0][0]
        assert "/estacao/A001/" in call_url
        assert "/estacao/dados/" not in call_url


class TestInmetEmptyResponse:
    @pytest.mark.asyncio
    async def test_non_list_response_returns_empty(self):
        resp = make_mock_response(200, json_data={"error": "unexpected"})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._get_json("/test")

        assert result == []

    @pytest.mark.asyncio
    async def test_empty_list_response(self):
        resp = make_mock_response(200, json_data=[])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._get_json("/test")

        assert result == []


class TestInmetValidation:
    @pytest.mark.asyncio
    async def test_invalid_tipo_raises(self):
        with pytest.raises(ValueError, match="Tipo deve ser"):
            await client.fetch_estacoes("X")

    @pytest.mark.asyncio
    async def test_inicio_after_fim_raises(self):
        with pytest.raises(ValueError, match="inicio.*deve ser"):
            await client.fetch_dados_estacao("A001", date(2024, 12, 31), date(2024, 1, 1))


class TestInmetFetchDadosEstacaoChunking:
    @pytest.mark.asyncio
    async def test_chunking_respects_max_days(self):
        resp = make_mock_response(200, json_data=[{"d": "1"}])
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.inmet.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_dados_estacao("A001", date(2022, 1, 1), date(2024, 1, 1))

        assert mock_client.get.call_count >= 2
        assert isinstance(result, list)
