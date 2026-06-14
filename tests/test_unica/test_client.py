from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.exceptions import ParseError, SourceUnavailableError
from agrobr.unica import client as unica_client
from tests.helpers import make_mock_async_client, make_mock_response

PAGINA_COM_PDF = (
    b"<html><iframe src='https://unicadata.com.br/arquivos/pdfs/2026/05/"
    b"3d26022108c8712d1a4a68dc4fbbb940.pdf'></iframe></html>"
)

PDF_VALIDO = b"%PDF-1.4" + b"\x00" * 20_000
XLSX_VALIDO = b"PK\x03\x04" + b"\x00" * 100


def _client_with_responses(*responses):
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(side_effect=list(responses))
    return mock_client


class TestFetchQuinzenalPdf:
    @pytest.mark.asyncio
    async def test_fluxo_pagina_e_pdf(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=PAGINA_COM_PDF),
            make_mock_response(200, content=PDF_VALIDO),
        )

        with patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client):
            content, url = await unica_client.fetch_quinzenal_pdf()

        assert content == PDF_VALIDO
        assert url == (
            "https://unicadata.com.br/arquivos/pdfs/2026/05/3d26022108c8712d1a4a68dc4fbbb940.pdf"
        )
        assert mock_client.get.call_count == 2
        assert "listagem.php?idMn=63" in mock_client.get.call_args_list[0][0][0]

    @pytest.mark.asyncio
    async def test_cache_evita_segundo_download_do_mesmo_pdf(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=PAGINA_COM_PDF),
            make_mock_response(200, content=PDF_VALIDO),
            make_mock_response(200, content=PAGINA_COM_PDF),
        )

        with patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client):
            content1, url1 = await unica_client.fetch_quinzenal_pdf()
            content2, url2 = await unica_client.fetch_quinzenal_pdf()

        assert content1 == content2 == PDF_VALIDO
        assert url1 == url2
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_pagina_sem_pdf_raises_parse_error(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=b"<html>sem iframe aqui</html>"),
        )

        with (
            patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(ParseError, match="PDF quinzenal"),
        ):
            await unica_client.fetch_quinzenal_pdf()

    @pytest.mark.asyncio
    async def test_pdf_pequeno_raises(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=PAGINA_COM_PDF),
            make_mock_response(200, content=b"%PDF-1.4 pequeno"),
        )

        with (
            patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="PDF inválido"),
        ):
            await unica_client.fetch_quinzenal_pdf()

    @pytest.mark.asyncio
    async def test_resposta_sem_magic_pdf_raises(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=PAGINA_COM_PDF),
            make_mock_response(200, content=b"<html>" + b"\x00" * 20_000),
        )

        with (
            patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="PDF inválido"),
        ):
            await unica_client.fetch_quinzenal_pdf()


class TestFetchHistoricoXlsx:
    @pytest.mark.asyncio
    async def test_params_do_form(self):
        mock_client = _client_with_responses(make_mock_response(200, content=XLSX_VALIDO))

        with patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client):
            content, url = await unica_client.fetch_historico_xlsx(
                "acucar", "2018/2019", "2020/2021"
            )

        assert content == XLSX_VALIDO
        params = mock_client.get.call_args[1]["params"]
        assert params["tipoHistorico"] == "2"
        assert params["idTabela"] == "2494"
        assert params["produto"] == "acucar"
        assert params["safraIni"] == "2018/2019"
        assert params["safraFim"] == "2020/2021"
        assert params["estado"].startswith("RS,SC,PR,SP")
        assert "produto=acucar" in url

    @pytest.mark.asyncio
    async def test_safras_default(self):
        mock_client = _client_with_responses(make_mock_response(200, content=XLSX_VALIDO))

        with patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client):
            await unica_client.fetch_historico_xlsx("cana")

        params = mock_client.get.call_args[1]["params"]
        assert params["safraIni"] == "1980/1981"
        assert params["safraFim"] == "2020/2021"

    @pytest.mark.asyncio
    async def test_safra_invalida_raises(self):
        with pytest.raises(ValueError, match="Formato esperado"):
            await unica_client.fetch_historico_xlsx("cana", "2019", None)

    @pytest.mark.asyncio
    async def test_resposta_nao_xlsx_raises(self):
        mock_client = _client_with_responses(
            make_mock_response(200, content=b"<html>erro 500 disfarcado</html>"),
        )

        with (
            patch("agrobr.unica.client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SourceUnavailableError, match="XLSX"),
        ):
            await unica_client.fetch_historico_xlsx("cana")
