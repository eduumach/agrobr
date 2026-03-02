import httpx
import pandas as pd
import pytest

from agrobr.datasets.silvicultura import SilviculturaDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2022,
                "localidade": "Minas Gerais",
                "localidade_cod": 31,
                "produto": "eucalipto_folha",
                "valor": 800000.0,
                "unidade": "Toneladas",
                "fonte": "ibge_silvicultura",
            },
        ]
    )


class TestSilviculturaFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("eucalipto_folha")

        assert len(df) == 1
        assert "valor" in df.columns
        assert "unidade" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("eucalipto_folha", return_meta=True)

        assert meta.dataset == "silvicultura"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_silvicultura"]
        assert meta.selected_source == "ibge_silvicultura"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = SilviculturaDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("soja")


class TestSilviculturaKwargs:
    @pytest.mark.asyncio
    async def test_passes_variavel_kwarg(self):
        mock_fn = make_source(_mock_df())
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("eucalipto_folha", variavel="valor_producao")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["variavel"] == "valor_producao"


class TestSilviculturaSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            pd.DataFrame(), raises=httpx.ConnectError("test")
        )

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("eucalipto_folha")
