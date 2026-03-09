from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.conab.progresso import client
from agrobr.conab.progresso.client import (
    _extract_plantio_link,
    _extract_week_links,
    fetch_latest,
    fetch_xlsx_semanal,
    list_semanas,
)
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import RETRY_SLEEP, make_mock_async_client, make_mock_response

PATCH_CLIENT = "agrobr.conab.progresso.client.httpx.AsyncClient"


def _week_page_html(links: list[tuple[str, str]]) -> str:
    anchors = "\n".join(f'<a href="{href}">{text}</a>' for text, href in links)
    return f"<html><body>{anchors}</body></html>"


def _plantio_page_html(xlsx_href: str) -> str:
    return f'<html><body><a href="{xlsx_href}">Plantio e Colheita</a></body></html>'


class TestExtractWeekLinks:
    def test_extracts_matching_links(self):
        html = _week_page_html(
            [
                ("Acompanhamento semanal", "/pt-br/acompanhamento-das-lavouras/sem1"),
                ("Acompanhamento quinzenal", "/pt-br/acompanhamento-das-lavouras/sem2"),
            ]
        )
        result = _extract_week_links(html)
        assert len(result) == 2
        assert result[0][0] == "Acompanhamento semanal"
        assert "acompanhamento-das-lavouras" in result[0][1]

    def test_ignores_non_matching_links(self):
        html = '<html><body><a href="/other">Acompanhamento</a></body></html>'
        result = _extract_week_links(html)
        assert result == []

    def test_ignores_links_without_acompanhamento_text(self):
        html = (
            '<html><body><a href="/acompanhamento-das-lavouras/sem1">Outro texto</a></body></html>'
        )
        result = _extract_week_links(html)
        assert result == []

    def test_deduplicates_hrefs(self):
        html = _week_page_html(
            [
                ("Acompanhamento A", "/pt-br/acompanhamento-das-lavouras/sem1"),
                ("Acompanhamento B", "/pt-br/acompanhamento-das-lavouras/sem1"),
            ]
        )
        result = _extract_week_links(html)
        assert len(result) == 1

    def test_absolute_url_preserved(self):
        html = (
            "<html><body>"
            '<a href="https://external.com/acompanhamento-das-lavouras/x">Acompanhamento X</a>'
            "</body></html>"
        )
        result = _extract_week_links(html)
        assert len(result) == 1
        assert result[0][1] == "https://external.com/acompanhamento-das-lavouras/x"

    def test_relative_url_gets_base_prefix(self):
        html = (
            "<html><body>"
            '<a href="/pt-br/acompanhamento-das-lavouras/y">Acompanhamento Y</a>'
            "</body></html>"
        )
        result = _extract_week_links(html)
        assert len(result) == 1
        assert result[0][1].startswith("https://www.gov.br/conab")

    def test_empty_html(self):
        result = _extract_week_links("<html><body></body></html>")
        assert result == []


class TestExtractPlantioLink:
    def test_finds_plantio_colheita_link(self):
        html = _plantio_page_html("/files/plantio_e_colheita.xlsx")
        result = _extract_plantio_link(html)
        assert result is not None
        assert "plantio" in result.lower()

    def test_returns_none_when_no_link(self):
        html = '<html><body><a href="/other">Other</a></body></html>'
        result = _extract_plantio_link(html)
        assert result is None

    def test_absolute_url_preserved(self):
        html = (
            '<html><body><a href="https://cdn.com/plantio_colheita.xlsx">Download</a></body></html>'
        )
        result = _extract_plantio_link(html)
        assert result == "https://cdn.com/plantio_colheita.xlsx"

    def test_relative_url_gets_base_prefix(self):
        html = '<html><body><a href="/files/plantio_colheita.xlsx">Download</a></body></html>'
        result = _extract_plantio_link(html)
        assert result is not None
        assert result.startswith("https://www.gov.br/conab")

    def test_case_insensitive_match(self):
        html = '<html><body><a href="/files/Plantio_Colheita.xlsx">Download</a></body></html>'
        result = _extract_plantio_link(html)
        assert result is not None


@pytest.mark.asyncio()
class TestListSemanas:
    async def test_single_page(self):
        page_html = _week_page_html(
            [
                ("Acompanhamento Sem1", "/pt-br/acompanhamento-das-lavouras/s1"),
            ]
        )
        resp = make_mock_response(200, text=page_html)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=1)

        assert len(result) == 1
        assert result[0][0] == "Acompanhamento Sem1"

    async def test_multiple_pages(self):
        page1_html = _week_page_html(
            [
                ("Acompanhamento P1", "/pt-br/acompanhamento-das-lavouras/p1"),
            ]
        )
        page2_html = _week_page_html(
            [
                ("Acompanhamento P2", "/pt-br/acompanhamento-das-lavouras/p2"),
            ]
        )
        resp1 = make_mock_response(200, text=page1_html)
        resp2 = make_mock_response(200, text=page2_html)
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp1, resp2])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=2)

        assert len(result) == 2

    async def test_stops_on_non_200(self):
        page1_html = _week_page_html(
            [
                ("Acompanhamento P1", "/pt-br/acompanhamento-das-lavouras/p1"),
            ]
        )
        resp1 = make_mock_response(200, text=page1_html)
        resp2 = make_mock_response(404, text="Not Found")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp1, resp2])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=3)

        assert len(result) == 1

    async def test_stops_on_empty_page(self):
        page1_html = _week_page_html(
            [
                ("Acompanhamento P1", "/pt-br/acompanhamento-das-lavouras/p1"),
            ]
        )
        resp1 = make_mock_response(200, text=page1_html)
        resp2 = make_mock_response(200, text="<html><body>No links</body></html>")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp1, resp2])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=3)

        assert len(result) == 1

    async def test_returns_empty_when_no_weeks(self):
        resp = make_mock_response(200, text="<html><body>Empty</body></html>")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=1)

        assert result == []

    async def test_first_page_non_200_returns_empty(self):
        resp = make_mock_response(404, text="Not Found")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            result = await list_semanas(max_pages=2)

        assert result == []


@pytest.mark.asyncio()
class TestFetchXlsxSemanal:
    async def test_success(self):
        xlsx_content = b"\x00" * 2000
        week_html = _plantio_page_html("https://cdn.com/plantio_colheita.xlsx")
        resp_week = make_mock_response(200, text=week_html)
        resp_xlsx = make_mock_response(
            200,
            content=xlsx_content,
            headers={
                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_week, resp_xlsx])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            content, url = await fetch_xlsx_semanal("https://example.com/week1")

        assert content == xlsx_content
        assert url == "https://cdn.com/plantio_colheita.xlsx"

    async def test_week_page_non_200_raises(self):
        resp = make_mock_response(404, text="Not Found")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError, match="HTTP 404"),
        ):
            await fetch_xlsx_semanal("https://example.com/week1")

    async def test_no_plantio_link_raises(self):
        resp = make_mock_response(200, text="<html><body>No xlsx link</body></html>")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(return_value=resp)

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError, match="plantio/colheita"),
        ):
            await fetch_xlsx_semanal("https://example.com/week1")

    async def test_xlsx_non_200_raises(self):
        week_html = _plantio_page_html("https://cdn.com/plantio_colheita.xlsx")
        resp_week = make_mock_response(200, text=week_html)
        resp_xlsx = make_mock_response(404, text="Not Found")
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_week, resp_xlsx])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError, match="HTTP 404"),
        ):
            await fetch_xlsx_semanal("https://example.com/week1")

    async def test_bad_content_type_small_file_raises(self):
        week_html = _plantio_page_html("https://cdn.com/plantio_colheita.xlsx")
        resp_week = make_mock_response(200, text=week_html)
        resp_xlsx = make_mock_response(
            200,
            content=b"tiny",
            headers={"content-type": "text/html"},
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_week, resp_xlsx])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
            pytest.raises(SourceUnavailableError, match="Content-Type"),
        ):
            await fetch_xlsx_semanal("https://example.com/week1")

    async def test_valid_content_type_spreadsheet(self):
        xlsx_content = b"\x00" * 500
        week_html = _plantio_page_html("https://cdn.com/plantio_colheita.xlsx")
        resp_week = make_mock_response(200, text=week_html)
        resp_xlsx = make_mock_response(
            200,
            content=xlsx_content,
            headers={
                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_week, resp_xlsx])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            content, url = await fetch_xlsx_semanal("https://example.com/week1")

        assert content == xlsx_content

    async def test_large_file_unknown_content_type_passes(self):
        xlsx_content = b"\x00" * 2000
        week_html = _plantio_page_html("https://cdn.com/plantio_colheita.xlsx")
        resp_week = make_mock_response(200, text=week_html)
        resp_xlsx = make_mock_response(
            200,
            content=xlsx_content,
            headers={"content-type": "application/octet-stream"},
        )
        mock_client = make_mock_async_client()
        mock_client.get = AsyncMock(side_effect=[resp_week, resp_xlsx])

        with (
            patch(PATCH_CLIENT, return_value=mock_client),
            patch(RETRY_SLEEP, new_callable=AsyncMock),
        ):
            content, url = await fetch_xlsx_semanal("https://example.com/week1")

        assert len(content) == 2000


@pytest.mark.asyncio()
class TestFetchLatest:
    async def test_success(self):
        xlsx_content = b"\x00" * 2000
        mock_weeks = [("Acompanhamento 02/02 a 08/02/26", "https://example.com/s1")]

        with (
            patch.object(client, "list_semanas", new_callable=AsyncMock, return_value=mock_weeks),
            patch.object(
                client,
                "fetch_xlsx_semanal",
                new_callable=AsyncMock,
                return_value=(xlsx_content, "https://cdn.com/file.xlsx"),
            ) as mock_fetch,
        ):
            content, url, desc = await fetch_latest()

        assert content == xlsx_content
        assert url == "https://cdn.com/file.xlsx"
        assert desc == "Acompanhamento 02/02 a 08/02/26"
        mock_fetch.assert_called_once_with("https://example.com/s1")

    async def test_no_weeks_raises(self):
        with (
            patch.object(client, "list_semanas", new_callable=AsyncMock, return_value=[]),
            pytest.raises(SourceUnavailableError, match="Nenhuma semana"),
        ):
            await fetch_latest()

    async def test_uses_first_week(self):
        mock_weeks = [
            ("Semana 1", "https://example.com/s1"),
            ("Semana 2", "https://example.com/s2"),
        ]

        with (
            patch.object(client, "list_semanas", new_callable=AsyncMock, return_value=mock_weeks),
            patch.object(
                client,
                "fetch_xlsx_semanal",
                new_callable=AsyncMock,
                return_value=(b"data", "https://cdn.com/f.xlsx"),
            ) as mock_fetch,
        ):
            _, _, desc = await fetch_latest()

        assert desc == "Semana 1"
        mock_fetch.assert_called_once_with("https://example.com/s1")

    async def test_max_pages_one(self):
        with (
            patch.object(
                client,
                "list_semanas",
                new_callable=AsyncMock,
                return_value=[("W", "https://u.com")],
            ) as mock_list,
            patch.object(
                client,
                "fetch_xlsx_semanal",
                new_callable=AsyncMock,
                return_value=(b"x", "https://cdn.com/x.xlsx"),
            ),
        ):
            await fetch_latest()

        mock_list.assert_called_once_with(max_pages=1)
