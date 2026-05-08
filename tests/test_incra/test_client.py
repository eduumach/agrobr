from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.exceptions import SourceUnavailableError


class TestFetchQuilombolas:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        from agrobr.incra.client import fetch_quilombolas

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            content, url = await fetch_quilombolas()
        assert len(content) >= 5000
        assert "CMR-PUBLICO" in url

    @pytest.mark.asyncio
    async def test_no_cql_in_url(self):
        from agrobr.incra.client import fetch_quilombolas

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas()
        assert "CQL_FILTER" not in url

    @pytest.mark.asyncio
    async def test_bbox_in_url(self):
        from agrobr.incra.client import fetch_quilombolas

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas(bbox=(-60.0, -15.0, -50.0, -10.0))
        assert "BBOX=" in url
        assert "CQL_FILTER" not in url

    @pytest.mark.asyncio
    async def test_404_raises(self):
        from agrobr.incra.client import fetch_quilombolas

        with (
            patch(
                "agrobr.incra.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(source="incra", url="", last_error="HTTP 404"),
            ),
            pytest.raises(SourceUnavailableError),
        ):
            await fetch_quilombolas()

    @pytest.mark.asyncio
    async def test_too_small_raises(self):
        from agrobr.incra.client import fetch_quilombolas

        with (
            patch(
                "agrobr.incra.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(
                    source="incra", url="", last_error="WFS response too small"
                ),
            ),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await fetch_quilombolas()


class TestFetchQuilombolasGeo:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        from agrobr.incra.client import fetch_quilombolas_geo

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            content, url = await fetch_quilombolas_geo()
        assert len(content) >= 5000
        assert "outputFormat=application/json" in url

    @pytest.mark.asyncio
    async def test_url_contains_geom_column(self):
        from agrobr.incra.client import fetch_quilombolas_geo

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas_geo()
        assert "propertyName=geom," in url

    @pytest.mark.asyncio
    async def test_max_features_in_url(self):
        from agrobr.incra.client import fetch_quilombolas_geo
        from agrobr.incra.models import MAX_FEATURES_GEO

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas_geo()
        assert f"maxFeatures={MAX_FEATURES_GEO}" in url

    @pytest.mark.asyncio
    async def test_no_cql_in_geo_url(self):
        from agrobr.incra.client import fetch_quilombolas_geo

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas_geo()
        assert "CQL_FILTER" not in url

    @pytest.mark.asyncio
    async def test_bbox_only_no_cql(self):
        from agrobr.incra.client import fetch_quilombolas_geo

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas_geo(bbox=(-60.0, -15.0, -50.0, -10.0))
        assert "BBOX=" in url
        assert "CQL_FILTER" not in url
