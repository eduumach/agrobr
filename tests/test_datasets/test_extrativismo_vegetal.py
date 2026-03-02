import httpx
import pandas as pd
import pytest

from agrobr.datasets.extrativismo_vegetal import ExtrativsmoVegetalDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2022,
                "localidade": "Pará",
                "localidade_cod": 15,
                "produto": "acai",
                "valor": 1500000.0,
                "unidade": "Toneladas",
                "fonte": "ibge_extracao_vegetal",
            },
        ]
    )


class TestExtrativsmoVegetalFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("acai")

        assert len(df) == 1
        assert "valor" in df.columns
        assert "unidade" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("acai", return_meta=True)

        assert meta.dataset == "extrativismo_vegetal"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_extracao_vegetal"]
        assert meta.selected_source == "ibge_extracao_vegetal"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ExtrativsmoVegetalDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("soja")


class TestExtrativsmoVegetalKwargs:
    @pytest.mark.asyncio
    async def test_passes_variavel_kwarg(self):
        mock_fn = make_source(_mock_df())
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("acai", variavel="valor_producao")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["variavel"] == "valor_producao"


class TestExtrativsmoVegetalSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            pd.DataFrame(), raises=httpx.ConnectError("test")
        )

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("acai")
