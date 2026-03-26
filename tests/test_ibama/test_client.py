from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.ibama.client import (
    _build_cql,
    fetch_embargos,
    fetch_embargos_geo,
)


class TestBuildCql:
    def test_uf_filter(self):
        assert _build_cql(uf="MT") == "sig_uf='MT'"

    def test_none_returns_none(self):
        assert _build_cql() is None


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

        with patch("agrobr.utils.geo.fetch_wfs", side_effect=mock_fetch_wfs):
            pages, base_url = await fetch_embargos()

        assert len(pages) == 2
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_zero_hits_returns_empty(self):
        hits_xml = (
            b'<?xml version="1.0"?><wfs:FeatureCollection numberMatched="0" numberReturned="0"/>'
        )

        with patch(
            "agrobr.utils.geo.fetch_wfs",
            new_callable=AsyncMock,
            return_value=hits_xml,
        ):
            pages, url = await fetch_embargos()

        assert pages == []

    @pytest.mark.asyncio
    async def test_404_raises(self):
        with (
            patch(
                "agrobr.utils.geo.fetch_wfs",
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
        with patch(
            "agrobr.ibama.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_embargos_geo()

        assert "outputFormat=application" in url

    @pytest.mark.asyncio
    async def test_geom_column_in_url(self):
        with patch(
            "agrobr.ibama.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_embargos_geo()

        assert "propertyName=geom," in url

    @pytest.mark.asyncio
    async def test_no_cql_in_geo_url(self):
        with patch(
            "agrobr.ibama.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_embargos_geo()

        assert "CQL_FILTER" not in url

    @pytest.mark.asyncio
    async def test_bbox_only_no_cql(self):
        with patch(
            "agrobr.ibama.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_embargos_geo(bbox=(-60.0, -15.0, -50.0, -10.0))

        assert "BBOX=" in url
        assert "CQL_FILTER" not in url
