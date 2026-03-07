import httpx
import pandas as pd
import pytest

from agrobr.datasets.importacao import IMPORTACAO_INFO, ImportacaoDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_df(**overrides):
    row = {
        "ano": 2024,
        "mes": 1,
        "produto": "soja",
        "uf": "SP",
        "kg_liquido": 1000000.0,
        "valor_fob_usd": 500000.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestImportacaoFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ImportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("soja", ano=2024)

        assert len(df) == 1
        assert "kg_liquido" in df.columns
        assert df.iloc[0]["valor_fob_usd"] == 500000.0

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ImportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("soja", ano=2024, return_meta=True)

        assert meta.dataset == "importacao"
        assert meta.contract_version == "1.0"
        assert "comexstat" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ImportacaoDataset()
        with pytest.raises(ValueError, match="Produto .* não suportado"):
            await dataset.fetch("banana", ano=2024)

    def test_normalize_adds_produto(self):
        df_no_produto = _make_df()
        df_no_produto = df_no_produto.drop(columns=["produto"])

        dataset = ImportacaoDataset()
        result = dataset._normalize(df_no_produto, "milho")
        assert "produto" in result.columns
        assert result.iloc[0]["produto"] == "milho"

    def test_normalize_empty_df(self):
        empty_df = pd.DataFrame(columns=["ano", "mes", "uf", "kg_liquido", "valor_fob_usd"])
        dataset = ImportacaoDataset()
        result = dataset._normalize(empty_df, "soja")
        assert "produto" in result.columns
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = ImportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja", ano=2024)


class TestImportacaoInfo:
    def test_single_source(self):
        assert len(IMPORTACAO_INFO.sources) == 1
        assert IMPORTACAO_INFO.sources[0].name == "comexstat"

    def test_products(self):
        assert "soja" in IMPORTACAO_INFO.products
        assert "milho" in IMPORTACAO_INFO.products
