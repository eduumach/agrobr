from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.funai.client import (
    _build_wfs_url,
    fetch_terras_indigenas,
    fetch_terras_indigenas_geo,
)
from agrobr.funai.models import PROPERTY_NAMES


class TestBuildWfsUrl:
    def test_url_contains_namespace_and_layer(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "Funai" in url
        assert "tis_poligonais" in url

    def test_url_uses_wfs_2_0_type_names(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "typeNames=" in url
        assert "typeName=" not in url or "typeNames=" in url

    def test_url_uses_count_not_max_features(self):
        url = _build_wfs_url(PROPERTY_NAMES, max_features=500)
        assert "count=500" in url
        assert "maxFeatures=" not in url

    def test_output_format_csv(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="csv")
        assert "outputFormat=csv" in url

    def test_output_format_json(self):
        url = _build_wfs_url(PROPERTY_NAMES, output_format="application/json")
        assert "outputFormat=application/json" in url

    def test_bbox_format(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=(-60.0, -15.0, -50.0, -10.0))
        assert "BBOX=-60.0,-15.0,-50.0,-10.0,EPSG:4674" in url

    def test_bbox_none_no_bbox_in_url(self):
        url = _build_wfs_url(PROPERTY_NAMES, bbox=None)
        assert "BBOX" not in url

    def test_cql_filter_uf(self):
        url = _build_wfs_url(PROPERTY_NAMES, cql_filter="uf_sigla='MT'")
        decoded = unquote(url)
        assert "uf_sigla='MT'" in decoded

    def test_cql_filter_fase(self):
        url = _build_wfs_url(PROPERTY_NAMES, cql_filter="fase_ti='Regularizada'")
        decoded = unquote(url)
        assert "fase_ti='Regularizada'" in decoded

    def test_version_2_0_0(self):
        url = _build_wfs_url(PROPERTY_NAMES)
        assert "version=2.0.0" in url


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
    async def test_cql_combined_uf_fase(self):
        with patch(
            "agrobr.funai.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
        ):
            _, url = await fetch_terras_indigenas_geo(uf="MT", fase="Regularizada")
        decoded = unquote(url)
        assert "uf_sigla='MT'" in decoded
        assert "fase_ti='Regularizada'" in decoded
        assert " AND " in decoded
