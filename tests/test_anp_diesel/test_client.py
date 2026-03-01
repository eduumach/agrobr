"""Testes para agrobr.alt.anp_diesel.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.alt.anp_diesel import client
from agrobr.alt.anp_diesel.models import (
    PRECOS_BRASIL_URL,
    PRECOS_ESTADOS_URL,
    PRECOS_MUNICIPIOS_URLS,
    VENDAS_DIESEL_CSV_URL,
)
from tests.helpers import make_mock_async_client, make_mock_response

FAKE_XLSX_BYTES = b"PK\x03\x04" + b"x" * 1500
FAKE_XLS_BYTES = b"\xd0\xcf\x11\xe0" + b"x" * 1500


@pytest.fixture
def _mock_retry():
    async def _passthrough(fn, **_kw):
        return await fn()

    with patch("agrobr.alt.anp_diesel.client.retry_on_status", side_effect=_passthrough) as mock:
        yield mock


class TestDownloadXlsx:
    @pytest.mark.asyncio
    async def test_download_ok(self, _mock_retry):
        resp = make_mock_response(200, content=FAKE_XLSX_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            result = await client.download_xlsx("https://example.com/test.xlsx")
            assert result == FAKE_XLSX_BYTES

    @pytest.mark.asyncio
    async def test_download_404(self, _mock_retry):
        resp = make_mock_response(404, content=FAKE_XLSX_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.download_xlsx("https://example.com/notfound.xlsx")

    @pytest.mark.asyncio
    async def test_download_timeout(self):
        with patch("agrobr.alt.anp_diesel.client.retry_on_status") as _mock_retry:
            _mock_retry.side_effect = httpx.TimeoutException("timeout")

            with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
                instance = make_mock_async_client()
                mock_client.return_value = instance

                with pytest.raises(httpx.TimeoutException):
                    await client.download_xlsx("https://example.com/test.xlsx")


class TestFetchPrecosMunicipios:
    @pytest.mark.asyncio
    async def test_periodo_valido(self, _mock_retry):
        resp = make_mock_response(200, content=FAKE_XLSX_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            result = await client.fetch_precos_municipios("2022-2023")
            assert result == FAKE_XLSX_BYTES

    @pytest.mark.asyncio
    async def test_periodo_invalido(self):
        with pytest.raises(ValueError, match="invalido"):
            await client.fetch_precos_municipios("1999-2000")


class TestFetchPrecosEstados:
    @pytest.mark.asyncio
    async def test_fetch_ok(self, _mock_retry):
        resp = make_mock_response(200, content=FAKE_XLSX_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            result = await client.fetch_precos_estados()
            assert result == FAKE_XLSX_BYTES


class TestFetchPrecosBrasil:
    @pytest.mark.asyncio
    async def test_fetch_ok(self, _mock_retry):
        resp = make_mock_response(200, content=FAKE_XLSX_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            result = await client.fetch_precos_brasil()
            assert result == FAKE_XLSX_BYTES


FAKE_CSV_BYTES = b"ANO;MES;GRANDE REGIAO;UNIDADE DA FEDERACAO;PRODUTO;VENDAS\n" + b"x" * 200


class TestFetchVendasM3:
    @pytest.mark.asyncio
    async def test_fetch_ok(self, _mock_retry):
        resp = make_mock_response(200, content=FAKE_CSV_BYTES)
        with patch("agrobr.alt.anp_diesel.client.httpx.AsyncClient") as mock_client:
            instance = make_mock_async_client()
            instance.get = AsyncMock(return_value=resp)
            mock_client.return_value = instance

            result = await client.fetch_vendas_m3()
            assert result == FAKE_CSV_BYTES


class TestClientConstants:
    def test_timeout_read_generous(self):
        assert client.TIMEOUT.read >= 120.0

    def test_headers_user_agent(self):
        from agrobr.http.user_agents import UserAgentRotator

        headers = UserAgentRotator.get_headers(source="anp_diesel")
        assert "User-Agent" in headers
        assert "Mozilla" in headers["User-Agent"]

    def test_urls_precos_municipios(self):
        for _periodo, url in PRECOS_MUNICIPIOS_URLS.items():
            assert url.startswith("https://www.gov.br/anp")

    def test_url_precos_estados(self):
        assert PRECOS_ESTADOS_URL.startswith("https://www.gov.br/anp")

    def test_url_precos_brasil(self):
        assert PRECOS_BRASIL_URL.startswith("https://www.gov.br/anp")

    def test_url_vendas_diesel_csv(self):
        assert VENDAS_DIESEL_CSV_URL.startswith("https://www.gov.br/anp")
