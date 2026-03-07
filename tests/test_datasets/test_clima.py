from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.clima import CLIMA_INFO, ClimaDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_inmet_df():
    return pd.DataFrame(
        {
            "mes": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "uf": ["SP", "SP"],
            "precip_acum_mm": [150.0, 120.0],
            "temp_media": [25.0, 26.0],
            "temp_max_media": [30.0, 31.0],
            "temp_min_media": [20.0, 21.0],
            "num_estacoes": pd.array([15, 15], dtype="Int64"),
        }
    )


def _mock_nasa_df():
    return pd.DataFrame(
        {
            "mes": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "uf": ["SP", "SP"],
            "precip_acum_mm": [145.0, 115.0],
            "temp_media": [24.5, 25.5],
            "temp_max_media": [29.5, 30.5],
            "temp_min_media": [19.5, 20.5],
            "umidade_media": [75.0, 72.0],
            "radiacao_media_mj": [18.0, 19.0],
            "vento_medio_ms": [2.5, 2.8],
            "lat": [-23.5, -23.5],
            "lon": [-46.6, -46.6],
        }
    )


class TestClimaInfo:
    def test_inmet_priority(self):
        inmet = next(s for s in CLIMA_INFO.sources if s.name == "inmet")
        nasa = next(s for s in CLIMA_INFO.sources if s.name == "nasa_power")
        assert inmet.priority < nasa.priority

    def test_products_empty(self):
        assert CLIMA_INFO.products == []

    def test_license_livre(self):
        assert CLIMA_INFO.license == "livre"


def _add_inmet_nullable_cols(df: pd.DataFrame) -> pd.DataFrame:
    df["fonte"] = "inmet"
    for col in ("umidade_media", "radiacao_media_mj", "vento_medio_ms"):
        df[col] = pd.array([pd.NA] * len(df), dtype="Float64")
    return df


def _add_nasa_nullable_cols(df: pd.DataFrame) -> pd.DataFrame:
    df["fonte"] = "nasa_power"
    df["num_estacoes"] = pd.array([pd.NA] * len(df), dtype="Int64")
    return df


class TestClimaFetchUF:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ClimaDataset()
        df_inmet = _add_inmet_nullable_cols(_mock_inmet_df())
        dataset.info.sources[0].fetch_fn = make_source(df_inmet)

        df = await dataset.fetch("SP", ano=2024)

        assert len(df) == 2
        assert "precip_acum_mm" in df.columns
        assert "fonte" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ClimaDataset()
        df_inmet = _add_inmet_nullable_cols(_mock_inmet_df())
        dataset.info.sources[0].fetch_fn = make_source(df_inmet)

        df, meta = await dataset.fetch("SP", ano=2024, return_meta=True)

        assert meta.dataset == "clima"
        assert meta.contract_version == "1.0"
        assert "inmet" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_uf_required(self):
        dataset = ClimaDataset()

        with pytest.raises(ValueError, match="uf é obrigatório"):
            await dataset.fetch()


class TestClimaFallback:
    @pytest.mark.asyncio
    async def test_inmet_fails_nasa_fallback(self):
        dataset = ClimaDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        df_nasa = _add_nasa_nullable_cols(_mock_nasa_df().drop(columns=["lat", "lon"]))
        dataset.info.sources[1].fetch_fn = make_source(df_nasa)

        df, meta = await dataset.fetch("SP", ano=2024, return_meta=True)

        assert meta.selected_source == "nasa_power"
        assert "inmet" in meta.attempted_sources
        assert "nasa_power" in meta.attempted_sources
        assert len(df) == 2

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        dataset = ClimaDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))
        dataset.info.sources[1].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("SP", ano=2024)


class TestClimaNormalize:
    @pytest.mark.asyncio
    async def test_normalize_uppercases_uf(self):
        dataset = ClimaDataset()
        df_inmet = _mock_inmet_df()
        df_inmet["uf"] = "sp"
        df_inmet = _add_inmet_nullable_cols(df_inmet)
        dataset.info.sources[0].fetch_fn = make_source(df_inmet)

        df = await dataset.fetch("sp", ano=2024)

        assert (df["uf"] == "SP").all()

    @pytest.mark.asyncio
    async def test_inmet_has_estacoes_nasa_null(self):
        dataset = ClimaDataset()
        df_inmet = _add_inmet_nullable_cols(_mock_inmet_df())
        dataset.info.sources[0].fetch_fn = make_source(df_inmet)

        df = await dataset.fetch("SP", ano=2024)

        assert df["num_estacoes"].notna().all()
        assert df["umidade_media"].isna().all()

    @pytest.mark.asyncio
    async def test_nasa_has_umidade_inmet_null(self):
        dataset = ClimaDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        df_nasa = _add_nasa_nullable_cols(_mock_nasa_df().drop(columns=["lat", "lon"]))
        dataset.info.sources[1].fetch_fn = make_source(df_nasa)

        df = await dataset.fetch("SP", ano=2024)

        assert df["umidade_media"].notna().all()
        assert df["num_estacoes"].isna().all()


class TestClimaEstacao:
    @pytest.mark.asyncio
    async def test_missing_dates_raises(self):
        dataset = ClimaDataset()

        with pytest.raises(ValueError, match="inicio e fim"):
            await dataset.fetch(estacao="A301")

    @pytest.mark.asyncio
    async def test_estacao_calls_inmet(self):
        dataset = ClimaDataset()
        mock_df = pd.DataFrame(
            {
                "data": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "estacao": ["A301", "A301"],
                "uf": ["SP", "SP"],
                "temp_media": [25.0, 26.0],
                "temp_max": [30.0, 31.0],
                "temp_min": [20.0, 21.0],
                "precipitacao_mm": [10.0, 0.0],
                "umidade_media": [75.0, 72.0],
                "radiacao_total_kj_m2": [18000.0, 19000.0],
            }
        )

        with patch("agrobr.inmet.estacao", new_callable=AsyncMock) as mock_estacao:
            mock_estacao.return_value = (mock_df, mock_source_meta())
            df, meta = await dataset.fetch(
                estacao="A301", inicio="2024-01-01", fim="2024-01-31", return_meta=True
            )

        assert meta.selected_source == "inmet"
        assert len(df) == 2
        mock_estacao.assert_called_once_with(
            "A301", "2024-01-01", "2024-01-31", agregacao="diario", return_meta=True
        )
