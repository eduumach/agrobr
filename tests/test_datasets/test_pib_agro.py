import httpx
import pandas as pd
import pytest

from agrobr.datasets.pib_agro import PIB_AGRO_INFO, PibAgroDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_df(**overrides):
    row = {
        "trimestre": "202401",
        "valor": 150000.0,
        "unidade": "R$ (milhões)",
        "setor": "agropecuaria",
        "precos": "corrente",
        "fonte": "ibge_pib",
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestPibAgroFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = PibAgroDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("agropecuaria")

        assert len(df) == 1
        assert "trimestre" in df.columns
        assert df.iloc[0]["valor"] == 150000.0

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = PibAgroDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("agropecuaria", return_meta=True)

        assert meta.dataset == "pib_agro"
        assert meta.contract_version == "1.0"
        assert "ibge" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = PibAgroDataset()
        with pytest.raises(ValueError, match="Produto .* não suportado"):
            await dataset.fetch("mineracao")

    def test_normalize_adds_setor_precos(self):
        df = pd.DataFrame(
            [{"trimestre": "202401", "valor": 100.0, "unidade": "R$", "fonte": "ibge_pib"}]
        )
        dataset = PibAgroDataset()
        result = dataset._normalize(df, "industria", "real_1995")
        assert result.iloc[0]["setor"] == "industria"
        assert result.iloc[0]["precos"] == "real_1995"

    def test_normalize_empty_df(self):
        empty_df = pd.DataFrame(columns=["trimestre", "valor", "unidade", "fonte"])
        dataset = PibAgroDataset()
        result = dataset._normalize(empty_df, "agropecuaria", "corrente")
        assert "setor" in result.columns
        assert "precos" in result.columns
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = PibAgroDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("agropecuaria")

    @pytest.mark.asyncio
    async def test_precos_kwarg_propagates(self):
        mock_fn = make_source(_make_df(precos="real_1995"))
        dataset = PibAgroDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("agropecuaria", precos="real_1995")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["precos"] == "real_1995"

    @pytest.mark.asyncio
    async def test_trimestre_kwarg_propagates(self):
        mock_fn = make_source(_make_df())
        dataset = PibAgroDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("agropecuaria", trimestre="202301")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["trimestre"] == "202301"


class TestPibAgroInfo:
    def test_single_source(self):
        assert len(PIB_AGRO_INFO.sources) == 1
        assert PIB_AGRO_INFO.sources[0].name == "ibge"

    def test_products(self):
        assert "agropecuaria" in PIB_AGRO_INFO.products
        assert "pib_total" in PIB_AGRO_INFO.products
