from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.cftc import client as cftc_client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
)

COT_SAMPLE = [
    {"report_date_as_yyyy_mm_dd": "2026-06-02T00:00:00.000", "cftc_contract_market_code": "005602"},
]


def _client_with(resp):
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(return_value=resp)
    return mock_client


class TestFetchCotQuery:
    @pytest.mark.asyncio
    async def test_where_com_codigos(self):
        mock_client = _client_with(make_mock_response(200, json_data=COT_SAMPLE))

        with patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client):
            await cftc_client.fetch_cot(["005602", "002602"])

        params = mock_client.get.call_args[1]["params"]
        assert "cftc_contract_market_code in('005602','002602')" in params["$where"]
        assert params["$limit"] == "50000"
        assert params["$order"] == "report_date_as_yyyy_mm_dd,cftc_contract_market_code"

    @pytest.mark.asyncio
    async def test_sem_datas_nao_filtra_periodo(self):
        mock_client = _client_with(make_mock_response(200, json_data=COT_SAMPLE))

        with patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client):
            await cftc_client.fetch_cot(["005602"])

        where = mock_client.get.call_args[1]["params"]["$where"]
        assert "report_date_as_yyyy_mm_dd" not in where

    @pytest.mark.asyncio
    async def test_start_end_no_where(self):
        mock_client = _client_with(make_mock_response(200, json_data=COT_SAMPLE))

        with patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client):
            await cftc_client.fetch_cot(["005602"], start="2026-01-01", end=date(2026, 6, 1))

        where = mock_client.get.call_args[1]["params"]["$where"]
        assert "report_date_as_yyyy_mm_dd >= '2026-01-01T00:00:00.000'" in where
        assert "report_date_as_yyyy_mm_dd <= '2026-06-01T00:00:00.000'" in where

    @pytest.mark.asyncio
    async def test_data_invalida_raises_value_error(self):
        with pytest.raises(ValueError):
            await cftc_client.fetch_cot(["005602"], start="01/06/2026")

    @pytest.mark.asyncio
    async def test_default_usa_futures_only(self):
        mock_client = _client_with(make_mock_response(200, json_data=COT_SAMPLE))

        with patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client):
            _, url = await cftc_client.fetch_cot(["005602"])

        assert "72hh-3qpy" in url
        assert "72hh-3qpy" in mock_client.get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_combined_troca_resource(self):
        mock_client = _client_with(make_mock_response(200, json_data=COT_SAMPLE))

        with patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client):
            _, url = await cftc_client.fetch_cot(["005602"], combined=True)

        assert "kh3c-gbw2" in url


class TestFetchCotErrors:
    @pytest.mark.asyncio
    async def test_resposta_vazia_raises(self):
        mock_client = _client_with(make_mock_response(200, json_data=[]))

        with (
            patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="Resposta vazia"),
        ):
            await cftc_client.fetch_cot(["005602"])

    @pytest.mark.asyncio
    async def test_resposta_dict_erro_socrata_raises(self):
        mock_client = _client_with(
            make_mock_response(200, json_data={"error": True, "message": "query error"})
        )

        with (
            patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="Resposta vazia"),
        ):
            await cftc_client.fetch_cot(["005602"])

    @pytest.mark.asyncio
    async def test_timeout_esgotado_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.cftc.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await cftc_client.fetch_cot(["005602"])
