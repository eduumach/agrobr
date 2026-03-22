from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.mapbiomas_alerta import api

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "mapbiomas_alerta" / "alertas_sample"


def _mock_records() -> list[dict]:
    return json.loads((GOLDEN_DIR / "response.json").read_text(encoding="utf-8"))


class TestAlertas:
    @pytest.fixture(autouse=True)
    def _mock_token(self):
        with patch.object(api.client, "_get_token", return_value="test-tok"):
            yield

    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ):
            df = await api.alertas(token="tok")
        assert len(df) == 5
        assert "alert_code" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ):
            df, meta = await api.alertas(token="tok", return_meta=True)
        assert meta.source == "mapbiomas_alerta"
        assert meta.source_method == "httpx+graphql"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ):
            result = await api.alertas(token="tok", as_polars=True)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=([], "url"),
        ):
            df = await api.alertas(token="tok")
        assert len(df) == 0

    @pytest.mark.asyncio
    async def test_sources_passthrough(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ) as mock_fetch:
            await api.alertas(token="tok", sources=["DETER", "SAD"])
        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["sources"] == ["DETER", "SAD"]

    @pytest.mark.asyncio
    async def test_bbox_converted_to_bounding_box(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ) as mock_fetch:
            await api.alertas(token="tok", bbox=(-55.0, -10.0, -50.0, -5.0))
        call_kwargs = mock_fetch.call_args[1]
        bb = call_kwargs["bounding_box"]
        assert bb == [-10.0, -55.0, -5.0, -50.0]

    @pytest.mark.asyncio
    async def test_token_passthrough(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ) as mock_fetch:
            await api.alertas(token="tok")
        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["token"] == "test-tok"


class TestAlertasGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.fixture(autouse=True)
    def _mock_token(self):
        with patch.object(api.client, "_get_token", return_value="test-tok"):
            yield

    @pytest.mark.asyncio
    async def test_returns_geodataframe(self):
        import geopandas as local_gpd

        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ):
            gdf = await api.alertas_geo(token="tok")
        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 5

    @pytest.mark.asyncio
    async def test_return_meta(self):
        records = _mock_records()
        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=(records, "url"),
        ):
            gdf, meta = await api.alertas_geo(token="tok", return_meta=True)
        assert meta.source == "mapbiomas_alerta"
        assert meta.source_method == "httpx+graphql+wkt"

    @pytest.mark.asyncio
    async def test_empty_result(self):
        import geopandas as local_gpd

        with patch.object(
            api.client,
            "fetch_alertas",
            new_callable=AsyncMock,
            return_value=([], "url"),
        ):
            gdf = await api.alertas_geo(token="tok")
        assert len(gdf) == 0
        assert isinstance(gdf, local_gpd.GeoDataFrame)


class TestAlertaInfo:
    @pytest.mark.asyncio
    async def test_returns_dict(self):
        with (
            patch.object(
                api.client,
                "fetch_alert_date_range",
                new_callable=AsyncMock,
                return_value=(
                    {
                        "minDetectedAt": "2020-01-15",
                        "maxDetectedAt": "2024-12-31",
                        "minPublishedAt": "2020-02-01",
                        "maxPublishedAt": "2024-12-31",
                    },
                    "url",
                ),
            ),
            patch.object(
                api.client,
                "fetch_last_publication",
                new_callable=AsyncMock,
                return_value=({"publishedAt": "2024-06-24T12:00:00Z", "total": 1000}, "url"),
            ),
        ):
            info = await api.alerta_info()
        assert "date_range" in info
        assert "last_publication" in info
        assert info["date_range"]["minDetectedAt"] == "2020-01-15"
        assert info["last_publication"]["total"] == 1000
