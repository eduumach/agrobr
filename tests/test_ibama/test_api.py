from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibama import api

GOLDEN = Path(__file__).parent.parent / "golden_data" / "ibama" / "termo_embargo_sample.csv"
ZIP_URL = "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo_csv.zip"


def _patch_fetch():
    return patch(
        "agrobr.ibama.api.client.fetch_embargos_zip",
        new_callable=AsyncMock,
        return_value=(GOLDEN.read_bytes(), ZIP_URL),
    )


class TestEmbargos:
    @pytest.mark.asyncio
    async def test_retorna_dataframe(self):
        with _patch_fetch():
            df = await api.embargos()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 40
        assert "seq_tad" in df.columns
        assert "area_embargada_ha" in df.columns

    @pytest.mark.asyncio
    async def test_filtro_uf(self):
        with _patch_fetch():
            df = await api.embargos(uf="MT")

        assert len(df) > 0
        assert (df["uf"] == "MT").all()

    @pytest.mark.asyncio
    async def test_uf_invalida_raises(self):
        with pytest.raises(ValueError):
            await api.embargos(uf="XX")

    @pytest.mark.asyncio
    async def test_seq_tad_vazio_preservado(self):
        with _patch_fetch():
            df = await api.embargos()

        assert df["seq_tad"].isna().sum() == 26
        assert df.loc[df["seq_tad"].isna(), "numero_tad"].notna().all()

    @pytest.mark.asyncio
    async def test_return_meta(self):
        with _patch_fetch():
            df, meta = await api.embargos(return_meta=True)

        assert meta.source == "ibama"
        assert meta.source_method == "httpx+zip+csv"
        assert meta.selected_source == "ibama_sifisc"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")

        with _patch_fetch():
            result = await api.embargos(as_polars=True)

        assert isinstance(result, pl.DataFrame)


class TestEmbargosGeo:
    @pytest.mark.asyncio
    async def test_retorna_geodataframe(self):
        gpd = pytest.importorskip("geopandas")

        with _patch_fetch():
            gdf = await api.embargos_geo()

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 24
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_geo_return_meta(self):
        pytest.importorskip("geopandas")

        with _patch_fetch():
            gdf, meta = await api.embargos_geo(return_meta=True)

        assert meta.source == "ibama"
        assert meta.source_method == "httpx+zip+csv+wkt"
        assert meta.selected_source == "ibama_sifisc"

    @pytest.mark.asyncio
    async def test_geo_filtro_uf(self):
        pytest.importorskip("geopandas")

        with _patch_fetch():
            gdf_all = await api.embargos_geo()
            alvo = gdf_all["uf"].iloc[0]
            gdf = await api.embargos_geo(uf=alvo)

        assert len(gdf) >= 1
        assert (gdf["uf"] == alvo).all()
