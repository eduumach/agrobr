from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.bcb import focus_client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import (
    RETRY_SLEEP,
    make_mock_async_client,
    make_mock_response,
)

FOCUS_RECORDS = [
    {
        "Indicador": "PIB Agropecuária",
        "Data": "2026-03-21",
        "DataReferencia": "2026",
        "Media": 3.5,
        "Mediana": 3.48,
        "DesvioPadrao": 0.25,
        "Minimo": 2.8,
        "Maximo": 4.2,
        "numeroRespondentes": 85,
        "baseCalculo": 0,
    },
    {
        "Indicador": "PIB Agropecuária",
        "Data": "2026-03-14",
        "DataReferencia": "2026",
        "Media": 3.45,
        "Mediana": 3.42,
        "DesvioPadrao": 0.24,
        "Minimo": 2.7,
        "Maximo": 4.1,
        "numeroRespondentes": 83,
        "baseCalculo": 0,
    },
]


class TestFocusUrlConstruction:
    @pytest.mark.asyncio
    async def test_url_contains_focus_base(self):
        resp = make_mock_response(200, json_data={"value": FOCUS_RECORDS})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            await focus_client.fetch_focus("PIB Agropecuária")

        url = mock_client.get.call_args[0][0]
        assert "Expectativas" in url
        assert "ExpectativasMercadoAnuais" in url

    @pytest.mark.asyncio
    async def test_filter_param_contains_indicator(self):
        resp = make_mock_response(200, json_data={"value": FOCUS_RECORDS})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            await focus_client.fetch_focus("IPCA")

        url = mock_client.get.call_args[0][0]
        assert "Indicador%20eq%20'IPCA'" in url
        assert "$orderby=Data%20desc" in url
        assert "$format=json" in url
        assert "+" not in url

    @pytest.mark.asyncio
    async def test_top_param_passed(self):
        resp = make_mock_response(200, json_data={"value": FOCUS_RECORDS})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            await focus_client.fetch_focus("PIB Total", top=50)

        url = mock_client.get.call_args[0][0]
        assert "$top=50" in url


class TestFocusQuoteEscaping:
    @pytest.mark.asyncio
    async def test_single_quote_escaped(self):
        resp = make_mock_response(200, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            await focus_client.fetch_focus("Indicador's test")

        url = mock_client.get.call_args[0][0]
        assert "Indicador''s%20test" in url


class TestFocusPagination:
    @pytest.mark.asyncio
    async def test_two_pages_collected(self):
        page1 = FOCUS_RECORDS
        page2 = [
            {
                "Indicador": "PIB Agropecuária",
                "Data": "2026-02-28",
                "DataReferencia": "2026",
                "Media": 3.35,
                "Mediana": 3.33,
                "DesvioPadrao": 0.22,
                "Minimo": 2.6,
                "Maximo": 3.9,
                "numeroRespondentes": 78,
                "baseCalculo": 0,
            },
        ]

        resp1 = make_mock_response(200, json_data={"value": page1})
        resp2 = make_mock_response(200, json_data={"value": page2})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp1, resp2])

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            records, _ = await focus_client.fetch_focus("PIB Agropecuária", top=2)

        assert len(records) == 3
        assert mock_client.get.call_count == 2

        second_call_url = mock_client.get.call_args_list[1][0][0]
        assert "$skip=2" in second_call_url


class TestFocusEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_value_returns_empty_list(self):
        resp = make_mock_response(200, json_data={"value": []})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            records, _ = await focus_client.fetch_focus("PIB Agropecuária")

        assert records == []

    @pytest.mark.asyncio
    async def test_missing_value_key_returns_empty(self):
        resp = make_mock_response(200, json_data={"odata.metadata": "..."})
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client):
            records, _ = await focus_client.fetch_focus("PIB Agropecuária")

        assert records == []


class TestFocusRetry:
    @pytest.mark.asyncio
    async def test_timeout_retried_raises_source_unavailable(self):
        mock_client = make_mock_async_client()
        mock_client.get.side_effect = httpx.TimeoutException("read timeout")

        with (
            patch("agrobr.bcb.focus_client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await focus_client.fetch_focus("PIB Agropecuária")
