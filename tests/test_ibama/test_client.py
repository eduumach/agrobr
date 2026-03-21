from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest

from agrobr.exceptions import ParseError, SourceUnavailableError
from agrobr.ibama.client import (
    _build_cql,
    _build_wfs_url,
    fetch_embargos,
    fetch_embargos_geo,
    fetch_hits,
)
from agrobr.ibama.models import PROPERTY_NAMES


class TestBuildWfsUrl:
    def test_url_contains_namespace_and_layer(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "publica" in url
        assert "vw_brasil_adm_embargo_a" in url

    def test_url_uses_wfs_2_0_type_names(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "typeNames=" in url

    def test_url_uses_count(self):
        url = _build_wfs_url(PROPERTY_NAMES, count=500)
        assert "count=500" in url

    def test_url_uses_start_index(self):
        url = _build_wfs_url(PROPERTY_NAMES, start_index=10000)
        assert "startIndex=10000" in url

    def test_output_format_csv(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="csv")
        assert "outputFormat=csv" in url

    def test_output_format_json(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="application/json")
        assert "outputFormat=application" in url

    def test_result_type_hits(self):
        url = _build_wfs_url(PROPERTY_NAMES, result_type="hits")
        assert "resultType=hits" in url

    def test_bbox_format(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=(-60.0, -15.0, -50.0, -10.0))
        assert "BBOX=-60.0,-15.0,-50.0,-10.0,EPSG:4674" in url

    def test_bbox_none_no_bbox_in_url(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=None)
        assert "BBOX" not in url

    def test_cql_filter(self):
        url = _build_wfs_url(PROPERTY_NAMES, cql_filter="sig_uf='MT'")
        decoded = unquote(url)
        assert "sig_uf='MT'" in decoded

    def test_version_2_0_0(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "version=2.0.0" in url


class TestBuildCql:
    def test_uf_filter(self):
        assert _build_cql(uf="MT") == "sig_uf='MT'"

    def test_uf_case_insensitive(self):
        assert _build_cql(uf="mt") == "sig_uf='MT'"

    def test_none_returns_none(self):
        assert _build_cql() is None

    def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            _build_cql(uf="INVALID")


class TestFetchHits:
    @pytest.mark.asyncio
    async def test_parse_number_matched(self):
        xml = b'<?xml version="1.0"?><wfs:FeatureCollection numberMatched="89214" numberReturned="0"/>'
        with patch(
            "agrobr.ibama.client.fetch_wfs",
            new_callable=AsyncMock,
            return_value=xml,
        ):
            count = await fetch_hits()
        assert count == 89214

    @pytest.mark.asyncio
    async def test_no_number_matched_raises(self):
        xml = b'<?xml version="1.0"?><wfs:FeatureCollection/>'
        with (
            patch(
                "agrobr.ibama.client.fetch_wfs",
                new_callable=AsyncMock,
                return_value=xml,
            ),
            pytest.raises(ParseError, match="numberMatched"),
        ):
            await fetch_hits()


class TestFetchEmbargos:
    @pytest.mark.asyncio
    async def test_paginated_fetch(self):
        hits_xml = b'<?xml version="1.0"?><wfs:FeatureCollection numberMatched="15000" numberReturned="0"/>'
        page_content = b"x" * 100

        call_count = 0

        async def mock_fetch_wfs(url, **_kwargs):
            nonlocal call_count
            call_count += 1
            if "resultType=hits" in url:
                return hits_xml
            return page_content

        with patch("agrobr.ibama.client.fetch_wfs", side_effect=mock_fetch_wfs):
            pages, base_url = await fetch_embargos()

        assert len(pages) == 2
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_zero_hits_returns_empty(self):
        hits_xml = (
            b'<?xml version="1.0"?><wfs:FeatureCollection numberMatched="0" numberReturned="0"/>'
        )

        with patch(
            "agrobr.ibama.client.fetch_wfs",
            new_callable=AsyncMock,
            return_value=hits_xml,
        ):
            pages, url = await fetch_embargos()

        assert pages == []

    @pytest.mark.asyncio
    async def test_404_raises(self):
        with (
            patch(
                "agrobr.ibama.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(
                    source="ibama", url="test", last_error="HTTP 404"
                ),
            ),
            pytest.raises(SourceUnavailableError),
        ):
            await fetch_embargos()


class TestFetchEmbargosGeo:
    @pytest.mark.asyncio
    async def test_output_format_json(self):
        calls: list[str] = []

        async def mock_fetch_wfs(url, **_kwargs):
            calls.append(url)
            return b"x" * 100

        with patch("agrobr.ibama.client.fetch_wfs", side_effect=mock_fetch_wfs):
            _, url = await fetch_embargos_geo()

        assert "outputFormat=application" in url

    @pytest.mark.asyncio
    async def test_geom_column_in_url(self):
        async def mock_fetch_wfs(_url, **_kwargs):
            return b"x" * 100

        with patch("agrobr.ibama.client.fetch_wfs", side_effect=mock_fetch_wfs):
            _, url = await fetch_embargos_geo()

        assert "propertyName=geom," in url
