"""Testes de resiliência HTTP para agrobr.bcb.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.bcb import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
    make_sleep_tracker,
)


class TestBcbTimeout:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_odata("CusteioRegiaoUFProduto")

        assert mock_client.get.call_count == client.BCB_MAX_RETRIES


class TestBcbHTTPErrors:
    @pytest.mark.asyncio
    async def test_http_500_retries(self):
        resp_500 = make_mock_response(500, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_odata("CusteioRegiaoUFProduto")

        assert mock_client.get.call_count == client.BCB_MAX_RETRIES

    @pytest.mark.asyncio
    async def test_http_429_retries(self):
        resp_429 = make_mock_response(429, json_data={"value": []})
        resp_ok = make_mock_response(200, json_data={"value": [{"id": 1}]})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_ok])

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._fetch_odata("CusteioRegiaoUFProduto")

        assert result["value"] == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_http_403_raises_via_raise_for_status(self):
        resp_403 = make_mock_response(403, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await client._fetch_odata("CusteioRegiaoUFProduto")


class TestBcbEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_value_list(self):
        resp = make_mock_response(200, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_credito_rural(finalidade="custeio")

        assert result == []

    @pytest.mark.asyncio
    async def test_missing_value_key(self):
        resp = make_mock_response(200, json_data={"odata.metadata": "..."})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_credito_rural(finalidade="custeio")

        assert result == []


class TestBcbRetry:
    @pytest.mark.asyncio
    async def test_backoff_exponential(self):
        resp_500 = make_mock_response(500, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        sleep_calls, track_sleep = make_sleep_tracker()

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, side_effect=track_sleep),
            pytest.raises(SourceUnavailableError),
        ):
            await client._fetch_odata("CusteioRegiaoUFProduto")

        assert len(sleep_calls) == client.BCB_MAX_RETRIES - 1
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] > sleep_calls[i - 1]


class TestBcbFetchCreditoRural:
    @pytest.mark.asyncio
    async def test_invalid_finalidade_raises(self):
        with pytest.raises(ValueError, match="Finalidade inválida"):
            await client.fetch_credito_rural(finalidade="invalida")

    @pytest.mark.asyncio
    async def test_client_side_filtering_safra(self):
        records = [
            {"AnoEmissao": "2023", "nomeProduto": "SOJA", "cdEstado": "51"},
            {"AnoEmissao": "2024", "nomeProduto": "SOJA", "cdEstado": "51"},
        ]
        resp = make_mock_response(200, json_data={"value": records})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client):
            result = await client.fetch_credito_rural(finalidade="custeio", safra_sicor="2023/2024")

        assert all(r["AnoEmissao"] == "2023" for r in result)


class TestBcbFallback:
    @pytest.mark.asyncio
    async def test_odata_fails_tries_bigquery(self):
        with (
            patch("agrobr.bcb.client.fetch_credito_rural", new_callable=AsyncMock) as mock_odata,
            patch(
                "agrobr.bcb.bigquery_client.fetch_credito_rural_bigquery",
                new_callable=AsyncMock,
            ) as mock_bq,
        ):
            mock_odata.side_effect = SourceUnavailableError(
                source="bcb", url="test", last_error="timeout"
            )
            mock_bq.return_value = [{"id": 1}]
            records, source = await client.fetch_credito_rural_with_fallback()

            assert source == "bigquery"
            assert records == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_http_403_triggers_bigquery_fallback(self):
        resp_403 = make_mock_response(403, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_403)

        with (
            patch("agrobr.bcb.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.bcb.bigquery_client.fetch_credito_rural_bigquery",
                new_callable=AsyncMock,
            ) as mock_bq,
        ):
            mock_bq.return_value = [{"id": 2}]
            records, source = await client.fetch_credito_rural_with_fallback()

        assert source == "bigquery"
        assert records == [{"id": 2}]

    @pytest.mark.asyncio
    async def test_network_error_triggers_bigquery_fallback(self):
        with (
            patch("agrobr.bcb.client.fetch_credito_rural", new_callable=AsyncMock) as mock_odata,
            patch(
                "agrobr.bcb.bigquery_client.fetch_credito_rural_bigquery",
                new_callable=AsyncMock,
            ) as mock_bq,
        ):
            mock_odata.side_effect = SourceUnavailableError(
                source="bcb", last_error="ConnectError: connection refused after 6 retries"
            )
            mock_bq.return_value = [{"id": 3}]
            records, source = await client.fetch_credito_rural_with_fallback()

            assert source == "bigquery"
            assert records == [{"id": 3}]

    @pytest.mark.asyncio
    async def test_timeout_triggers_bigquery_fallback(self):
        with (
            patch("agrobr.bcb.client.fetch_credito_rural", new_callable=AsyncMock) as mock_odata,
            patch(
                "agrobr.bcb.bigquery_client.fetch_credito_rural_bigquery",
                new_callable=AsyncMock,
            ) as mock_bq,
        ):
            mock_odata.side_effect = SourceUnavailableError(
                source="bcb", last_error="TimeoutException: read timeout after 6 retries"
            )
            mock_bq.return_value = [{"id": 4}]
            records, source = await client.fetch_credito_rural_with_fallback()

            assert source == "bigquery"
            assert records == [{"id": 4}]
