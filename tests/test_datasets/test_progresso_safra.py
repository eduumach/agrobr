from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.deterministic import deterministic
from agrobr.datasets.progresso_safra import (
    PROGRESSO_SAFRA_INFO,
    ProgressoSafraDataset,
    progresso_safra,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _make_df(**overrides):
    row = {
        "cultura": "Soja",
        "safra": "2024/25",
        "operacao": "Semeadura",
        "estado": "MT",
        "semana_atual": "2024-11-15",
        "pct_ano_anterior": 0.85,
        "pct_semana_anterior": 0.90,
        "pct_semana_atual": 0.92,
        "pct_media_5_anos": 0.88,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestProgressoSafraFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "cultura" in df.columns
        assert df.iloc[0]["pct_semana_atual"] == 0.92

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "progresso_safra"
        assert meta.contract_version == "1.0"
        assert "conab" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ProgressoSafraDataset()
        with pytest.raises(ValueError, match="Produto .* não suportado"):
            await dataset.fetch("cana")

    def test_normalize_passthrough(self):
        df = _make_df()
        dataset = ProgressoSafraDataset()
        result = dataset._normalize(df.copy())
        pd.testing.assert_frame_equal(result, df)

    def test_normalize_empty_df(self):
        empty_df = pd.DataFrame(
            columns=[
                "cultura",
                "safra",
                "operacao",
                "estado",
                "semana_atual",
                "pct_ano_anterior",
                "pct_semana_anterior",
                "pct_semana_atual",
                "pct_media_5_anos",
            ]
        )
        dataset = ProgressoSafraDataset()
        result = dataset._normalize(empty_df)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")

    @pytest.mark.asyncio
    async def test_produto_normalizado(self):
        mock_fn = make_source(_make_df())
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("soja")

        call_args = mock_fn.call_args
        assert call_args[0][0] == "soja"

    @pytest.mark.asyncio
    async def test_forwards_estado_operacao(self):
        mock_fn = make_source(_make_df())
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("soja", estado="MT", operacao="Semeadura")

        _, kwargs = mock_fn.call_args
        assert kwargs["estado"] == "MT"
        assert kwargs["operacao"] == "Semeadura"

    @pytest.mark.asyncio
    async def test_snapshot_in_meta(self):
        dataset = ProgressoSafraDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())

        async with deterministic("2024-11-15"):
            df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.snapshot == "2024-11-15"


class TestProgressoSafraInfo:
    def test_single_source(self):
        assert len(PROGRESSO_SAFRA_INFO.sources) == 1
        assert PROGRESSO_SAFRA_INFO.sources[0].name == "conab"

    def test_products(self):
        assert "soja" in PROGRESSO_SAFRA_INFO.products
        assert "milho_1" in PROGRESSO_SAFRA_INFO.products
        assert "milho_2" in PROGRESSO_SAFRA_INFO.products

    def test_all_products(self):
        expected = ["algodao", "arroz", "feijao_1", "milho_1", "milho_2", "soja", "trigo"]
        assert PROGRESSO_SAFRA_INFO.products == expected


class TestProgressoSafraPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        with patch.object(ProgressoSafraDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _make_df()
            await progresso_safra("soja", estado="MT", operacao="Semeadura")

            mock_fetch.assert_called_once_with(
                "soja", estado="MT", operacao="Semeadura", return_meta=False
            )

    @pytest.mark.asyncio
    async def test_public_function_return_meta(self):
        with patch.object(ProgressoSafraDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (_make_df(), mock_source_meta())
            result = await progresso_safra("soja", return_meta=True)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], pd.DataFrame)

    @pytest.mark.asyncio
    async def test_public_function_forwards_kwargs(self):
        with patch.object(ProgressoSafraDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _make_df()
            await progresso_safra("soja", estado="PR", operacao="Colheita")

            _, kwargs = mock_fetch.call_args
            assert kwargs["estado"] == "PR"
            assert kwargs["operacao"] == "Colheita"
