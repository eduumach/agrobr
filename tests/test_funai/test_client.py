from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.funai.client import (
    fetch_terras_indigenas,
    fetch_terras_indigenas_geo,
)


class TestFetchTerrasIndigenas:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            data, url = await fetch_terras_indigenas()
        assert len(data) >= 100
        assert "typeNames=" in url

    @pytest.mark.asyncio
    async def test_404_raises(self):
        with (
            patch(
                "agrobr.funai.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(source="funai", url="", last_error="HTTP 404"),
            ),
            pytest.raises(SourceUnavailableError),
        ):
            await fetch_terras_indigenas()

    @pytest.mark.asyncio
    async def test_too_small_response_raises(self):
        with (
            patch(
                "agrobr.funai.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(
                    source="funai", url="", last_error="WFS response too small"
                ),
            ),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await fetch_terras_indigenas()


class TestFetchTerrasIndigenasGeo:
    @pytest.mark.asyncio
    async def test_output_format_json(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_terras_indigenas_geo()
        assert "outputFormat=application/json" in url

    @pytest.mark.asyncio
    async def test_geom_column_in_url(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_terras_indigenas_geo()
        assert "propertyName=the_geom," in url

    @pytest.mark.asyncio
    async def test_no_cql_in_geo_url(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_terras_indigenas_geo()
        assert "CQL_FILTER" not in url

    @pytest.mark.asyncio
    async def test_bbox_only_no_cql(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_terras_indigenas_geo(bbox=(-60.0, -15.0, -50.0, -10.0))
        assert "BBOX=" in url
        assert "CQL_FILTER" not in url
