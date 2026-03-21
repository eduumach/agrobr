from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.icmbio.client import _build_wfs_url, fetch_ucs, fetch_ucs_geo


class TestBuildWfsUrl:
    def test_url_contains_namespace_and_layer(self):
        url = _build_wfs_url(["cnuc", "nomeuc"])
        assert "ICMBio" in url
        assert "limiteucsfederais_a" in url

    def test_wfs_version_1_1_0(self):
        url = _build_wfs_url(["cnuc"])
        assert "version=1.1.0" in url

    def test_typename_singular(self):
        url = _build_wfs_url(["cnuc"])
        assert "typeName=" in url
        assert "typeNames=" not in url

    def test_max_features_not_count(self):
        url = _build_wfs_url(["cnuc"], max_features=100)
        assert "maxFeatures=100" in url
        assert "count=" not in url

    def test_output_format_csv(self):
        url = _build_wfs_url(["cnuc"], output_format="csv")
        assert "outputFormat=csv" in url

    def test_output_format_json(self):
        url = _build_wfs_url(["cnuc"], output_format="application/json")
        assert "outputFormat=application" in url

    def test_bbox_in_url(self):
        url = _build_wfs_url(["cnuc"], bbox=(-60.0, -20.0, -50.0, -10.0))
        assert "BBOX=-60.0,-20.0,-50.0,-10.0,EPSG:4674" in url

    def test_bbox_none_no_bbox(self):
        url = _build_wfs_url(["cnuc"])
        assert "BBOX" not in url

    def test_cql_filter_uf_like(self):
        url = _build_wfs_url(["cnuc"], cql_filter="ufabrang LIKE '%MT%'")
        decoded = unquote(url)
        assert "ufabrang LIKE '%MT%'" in decoded

    def test_cql_filter_grupo(self):
        url = _build_wfs_url(["cnuc"], cql_filter="grupouc='PI'")
        decoded = unquote(url)
        assert "grupouc='PI'" in decoded

    def test_geom_column_in_property_name(self):
        from agrobr.icmbio.models import PROPERTY_NAMES_GEO

        url = _build_wfs_url(PROPERTY_NAMES_GEO)
        assert "propertyName=the_geom," in url


class TestFetchUcs:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            content, url = await fetch_ucs()
        assert len(content) >= 5000
        assert "ICMBio" in url

    @pytest.mark.asyncio
    async def test_404_raises(self):
        with (
            patch(
                "agrobr.icmbio.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(source="icmbio", url="", last_error="HTTP 404"),
            ),
            pytest.raises(SourceUnavailableError),
        ):
            await fetch_ucs()

    @pytest.mark.asyncio
    async def test_too_small_raises(self):
        with (
            patch(
                "agrobr.icmbio.client.fetch_wfs",
                new_callable=AsyncMock,
                side_effect=SourceUnavailableError(
                    source="icmbio", url="", last_error="WFS response too small"
                ),
            ),
            pytest.raises(SourceUnavailableError, match="too small"),
        ):
            await fetch_ucs()

    @pytest.mark.asyncio
    async def test_uf_filter_cql(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_ucs(uf="MT")
        decoded = unquote(url)
        assert "ufabrang LIKE '%MT%'" in decoded

    @pytest.mark.asyncio
    async def test_grupo_filter_cql(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_ucs(grupo="PI")
        decoded = unquote(url)
        assert "grupouc='PI'" in decoded

    @pytest.mark.asyncio
    async def test_combined_filters(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_ucs(uf="MT", grupo="PI")
        decoded = unquote(url)
        assert "ufabrang LIKE '%MT%'" in decoded
        assert "grupouc='PI'" in decoded
        assert " AND " in decoded


class TestFetchUcsGeo:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            content, url = await fetch_ucs_geo()
        assert len(content) >= 5000

    @pytest.mark.asyncio
    async def test_output_format_json(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_ucs_geo()
        assert "outputFormat=application" in url

    @pytest.mark.asyncio
    async def test_geom_column_in_url(self):
        with patch(
            "agrobr.icmbio.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 5000
        ):
            _, url = await fetch_ucs_geo()
        assert "propertyName=the_geom," in url
