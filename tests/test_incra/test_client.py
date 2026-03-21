from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.incra.client import _build_cql, _build_wfs_url
from agrobr.incra.models import NAMESPACE, PROPERTY_NAMES, PROPERTY_NAMES_GEO


class TestBuildWfsUrl:
    def test_url_contains_namespace(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert f"typeName={NAMESPACE}:" in url

    def test_uses_typeName_singular(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "typeName=" in url
        assert "typeNames=" not in url

    def test_uses_maxFeatures(self):
        url = _build_wfs_url(PROPERTY_NAMES, max_features=100)
        assert "maxFeatures=100" in url
        assert "count=" not in url

    def test_output_format_csv(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="csv")
        assert "outputFormat=csv" in url

    def test_output_format_json(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="application/json")
        assert "outputFormat=application/json" in url

    def test_bbox_in_url(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=(-50.0, -15.0, -45.0, -10.0))
        assert "BBOX=-50.0,-15.0,-45.0,-10.0,EPSG:4674" in url

    def test_bbox_none_no_bbox(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=None)
        assert "BBOX" not in url

    def test_geom_column_in_geo_property_names(self):
        url = _build_wfs_url(PROPERTY_NAMES_GEO)
        assert "propertyName=the_geom," in url


class TestBuildCql:
    def test_uf_filter(self):
        cql = _build_cql(uf="MT")
        assert cql is not None
        assert "sg_uf='MT'" in cql

    def test_fase_filter(self):
        cql = _build_cql(fase="Titulada")
        assert cql is not None
        assert "ds_fase='Titulada'" in cql

    def test_combined_filter(self):
        cql = _build_cql(uf="MT", fase="Titulada")
        assert cql is not None
        assert "sg_uf='MT'" in cql
        assert "ds_fase='Titulada'" in cql
        assert " AND " in cql

    def test_no_filters(self):
        cql = _build_cql()
        assert cql is None

    def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            _build_cql(uf="INVALID")


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
    async def test_with_uf_and_fase(self):
        from agrobr.incra.client import fetch_quilombolas

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            content, url = await fetch_quilombolas(uf="MT", fase="Titulada")
        decoded = unquote(url)
        assert "sg_uf='MT'" in decoded
        assert "ds_fase='Titulada'" in decoded

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
        assert "propertyName=the_geom," in url

    @pytest.mark.asyncio
    async def test_max_features_500(self):
        from agrobr.incra.client import fetch_quilombolas_geo

        with patch(
            "agrobr.incra.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_quilombolas_geo()
        assert "maxFeatures=500" in url
