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
    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            df = await api.alertas(token="tok")

        assert len(df) == 5
        assert "alert_code" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            df, meta = await api.alertas(token="tok", return_meta=True)

        assert meta.source == "mapbiomas_alerta"
        assert meta.source_method == "httpx+graphql"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            result = await api.alertas(token="tok", as_polars=True)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_uf_filter(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            df = await api.alertas(token="tok", uf="PA")

        assert all(df["uf"] == "PA")

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.alertas(token="tok", uf="INVALID")

    @pytest.mark.asyncio
    async def test_invalid_source_raises(self):
        with pytest.raises(ValueError, match="Fontes invalidas"):
            await api.alertas(token="tok", sources=["INVALID_SOURCE"])

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=([], "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            df = await api.alertas(token="tok")

        assert len(df) == 0

    @pytest.mark.asyncio
    async def test_sources_passthrough(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ) as mock_fetch,
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            await api.alertas(token="tok", sources=["DETER", "SAD"])

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["sources"] == ["DETER", "SAD"]


class TestAlertasGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.mark.asyncio
    async def test_returns_geodataframe(self):
        import geopandas as local_gpd

        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            gdf = await api.alertas_geo(token="tok")

        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 5

    @pytest.mark.asyncio
    async def test_return_meta(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            gdf, meta = await api.alertas_geo(token="tok", return_meta=True)

        assert meta.source == "mapbiomas_alerta"
        assert meta.source_method == "httpx+graphql+wkt"

    @pytest.mark.asyncio
    async def test_uf_filter(self):
        records = _mock_records()
        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=(records, "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
        ):
            gdf = await api.alertas_geo(token="tok", uf="MT")

        assert all(gdf["uf"] == "MT")

    @pytest.mark.asyncio
    async def test_empty_result(self):
        import geopandas as local_gpd

        with (
            patch.object(
                api.client,
                "fetch_alertas",
                new_callable=AsyncMock,
                return_value=([], "url"),
            ),
            patch.object(api.client, "_get_token", return_value="tok"),
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
                return_value=({"minDate": "2020-01-01", "maxDate": "2024-12-31"}, "url"),
            ),
            patch.object(
                api.client,
                "fetch_last_publication",
                new_callable=AsyncMock,
                return_value=({"date": "2024-06-24", "alertsCount": 1000}, "url"),
            ),
        ):
            info = await api.alerta_info()

        assert "date_range" in info
        assert "last_publication" in info
        assert info["date_range"]["minDate"] == "2020-01-01"
        assert info["last_publication"]["alertsCount"] == 1000
