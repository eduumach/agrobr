"""Testes de resiliência HTTP para agrobr.antaq.client."""

from __future__ import annotations

import io
import zipfile
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agrobr.antaq import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import make_mock_async_client, make_mock_response

RETRY_SLEEP = "agrobr.http.retry.asyncio.sleep"

_ANTAQ_URL = "https://web3.antaq.gov.br/ea/txt/2024.zip"


def _make_zip(files: dict[str, str], *, min_size: int = 0) -> bytes:
    """Cria ZIP em memória com conteúdo dado.

    Se *min_size* > 0 e o ZIP for menor, padding é adicionado como
    arquivo extra para ultrapassar o limite.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content.encode("utf-8-sig"))
    data = buf.getvalue()
    if min_size and len(data) < min_size:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
            for name, content in files.items():
                zf.writestr(name, content.encode("utf-8-sig"))
            zf.writestr("_padding.bin", bytes(range(256)) * ((min_size // 256) + 2))
        data = buf.getvalue()
    return data


class TestDownloadZip:
    @pytest.mark.asyncio
    async def test_success(self):
        zip_bytes = _make_zip({"test.txt": "hello"}, min_size=500)
        resp = make_mock_response(200, content=zip_bytes, url=_ANTAQ_URL)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with patch("agrobr.antaq.client.httpx.AsyncClient", return_value=mock_client):
            result = await client._download_zip(_ANTAQ_URL)

        assert result == zip_bytes

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with (
            patch("agrobr.antaq.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.TimeoutException),
        ):
            await client._download_zip(_ANTAQ_URL)

    @pytest.mark.asyncio
    async def test_500_retries_then_raises(self):
        resp_500 = make_mock_response(500, content=b"", url=_ANTAQ_URL)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp_500)

        with (
            patch("agrobr.antaq.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError),
        ):
            await client._download_zip(_ANTAQ_URL)

        assert mock_client.get.call_count > 1

    @pytest.mark.asyncio
    async def test_429_retries_then_succeeds(self):
        zip_bytes = _make_zip({"test.txt": "ok"}, min_size=500)
        resp_429 = make_mock_response(429, content=b"", url=_ANTAQ_URL)
        resp_ok = make_mock_response(200, content=zip_bytes, url=_ANTAQ_URL)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_429, resp_ok])

        with (
            patch("agrobr.antaq.client.httpx.AsyncClient", return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await client._download_zip(_ANTAQ_URL)

        assert result == zip_bytes


class TestExtractTxtFromZip:
    def test_extracts_utf8_sig(self):
        content = "IDAtracacao;Porto\n1;Santos"
        zip_bytes = _make_zip({"2024Atracacao.txt": content})

        result = client._extract_txt_from_zip(zip_bytes, "2024Atracacao.txt")

        assert "IDAtracacao" in result
        assert "Santos" in result

    def test_missing_file_raises_keyerror(self):
        zip_bytes = _make_zip({"other.txt": "data"})

        with pytest.raises(KeyError):
            client._extract_txt_from_zip(zip_bytes, "missing.txt")

    def test_strips_bom(self):
        content = "colA;colB\n1;2"
        zip_bytes = _make_zip({"file.txt": content})

        result = client._extract_txt_from_zip(zip_bytes, "file.txt")

        assert not result.startswith("\ufeff")
        assert result.startswith("colA")


class TestListZipContents:
    def test_lists_files(self):
        zip_bytes = _make_zip(
            {
                "2024Atracacao.txt": "a",
                "2024Carga.txt": "b",
            }
        )

        names = client.list_zip_contents(zip_bytes)

        assert "2024Atracacao.txt" in names
        assert "2024Carga.txt" in names
        assert len(names) == 2


class TestFetchAnoZip:
    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        zip_bytes = _make_zip({"test.txt": "ok"})

        with patch.object(
            client, "_download_zip", new_callable=AsyncMock, return_value=zip_bytes
        ) as mock:
            result = await client.fetch_ano_zip(2024)

        mock.assert_called_once_with("https://web3.antaq.gov.br/ea/txt/2024.zip")
        assert result == zip_bytes


class TestFetchMercadoriaZip:
    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        zip_bytes = _make_zip({"Mercadoria.txt": "ok"})

        with patch.object(
            client, "_download_zip", new_callable=AsyncMock, return_value=zip_bytes
        ) as mock:
            result = await client.fetch_mercadoria_zip()

        mock.assert_called_once_with("https://web3.antaq.gov.br/ea/txt/Mercadoria.zip")
        assert result == zip_bytes


class TestExtractHelpers:
    def test_extract_atracacao(self):
        zip_bytes = _make_zip({"2024Atracacao.txt": "IDAtracacao;Porto\n1;Santos"})

        result = client.extract_atracacao(zip_bytes, 2024)

        assert "IDAtracacao" in result

    def test_extract_carga(self):
        zip_bytes = _make_zip({"2024Carga.txt": "IDCarga;IDAtracacao\n1;1"})

        result = client.extract_carga(zip_bytes, 2024)

        assert "IDCarga" in result

    def test_extract_mercadoria(self):
        zip_bytes = _make_zip({"Mercadoria.txt": "CDMercadoria;Mercadoria\n0901;Cafe"})

        result = client.extract_mercadoria(zip_bytes)

        assert "CDMercadoria" in result
