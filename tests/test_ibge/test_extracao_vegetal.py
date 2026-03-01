from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibge import client

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ibge" / "extracao_vegetal_sample"


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


class TestVariaveisExtracaoVegetal:
    def test_quantidade_produzida(self):
        assert client.VARIAVEIS_EXTRACAO_VEGETAL["quantidade_produzida"] == "144"

    def test_valor_producao(self):
        assert client.VARIAVEIS_EXTRACAO_VEGETAL["valor_producao"] == "145"

    def test_codes_numeric(self):
        for name, code in client.VARIAVEIS_EXTRACAO_VEGETAL.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


class TestProdutosExtracaoVegetal:
    def test_contains_acai(self):
        assert "acai" in client.PRODUTOS_EXTRACAO_VEGETAL
        assert client.PRODUTOS_EXTRACAO_VEGETAL["acai"] == "3403"

    def test_contains_castanha_para(self):
        assert "castanha_para" in client.PRODUTOS_EXTRACAO_VEGETAL

    def test_contains_erva_mate(self):
        assert "erva_mate" in client.PRODUTOS_EXTRACAO_VEGETAL

    def test_has_21_products(self):
        assert len(client.PRODUTOS_EXTRACAO_VEGETAL) == 21

    def test_all_codes_numeric(self):
        for name, code in client.PRODUTOS_EXTRACAO_VEGETAL.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


class TestUnidadesExtracaoVegetal:
    def test_acai_toneladas(self):
        assert client.UNIDADES_EXTRACAO_VEGETAL["acai"] == "Toneladas"

    def test_lenha_metros_cubicos(self):
        assert client.UNIDADES_EXTRACAO_VEGETAL["lenha"] == "Metros cúbicos"

    def test_madeira_tora_metros_cubicos(self):
        assert client.UNIDADES_EXTRACAO_VEGETAL["madeira_tora"] == "Metros cúbicos"

    def test_all_products_have_unit(self):
        for prod in client.PRODUTOS_EXTRACAO_VEGETAL:
            assert prod in client.UNIDADES_EXTRACAO_VEGETAL, f"{prod} missing"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestExtracaoVegetalValidation:
    async def test_produto_invalido(self):
        from agrobr.ibge import extracao_vegetal

        with pytest.raises(ValueError, match="Produto não suportado"):
            await extracao_vegetal("banana_inexistente")

    async def test_variavel_invalida(self):
        from agrobr.ibge import extracao_vegetal

        with pytest.raises(ValueError, match="Variável não suportada"):
            await extracao_vegetal("acai", variavel="peso")


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _build_mock_df(n_ufs=3):
    rows = []
    ufs = [("15", "Pará"), ("13", "Amazonas"), ("21", "Maranhão")][:n_ufs]
    for cod, nome in ufs:
        rows.append(
            {
                "D1C": cod,
                "D1N": nome,
                "D2C": "2023",
                "D2N": "2023",
                "D3C": "144",
                "D3N": "Quantidade produzida na extração vegetal",
                "D4C": "3403",
                "D4N": "Açaí (fruto)",
                "V": str(500000 + int(cod) * 10000),
                "NC": "3",
                "NN": "Unidade da Federação",
                "MC": "23",
                "MN": "Toneladas",
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mocked
# ---------------------------------------------------------------------------


class TestExtracaoVegetalMocked:
    async def test_returns_dataframe(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    async def test_output_columns(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023)
            expected = [
                "ano",
                "localidade",
                "localidade_cod",
                "produto",
                "valor",
                "unidade",
                "fonte",
            ]
            assert list(df.columns) == expected

    async def test_produto_enrichment(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023)
            assert (df["produto"] == "acai").all()

    async def test_unidade_toneladas(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023)
            assert (df["unidade"] == "Toneladas").all()

    async def test_fonte(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023)
            assert (df["fonte"] == "ibge_extracao_vegetal").all()

    async def test_fetch_sidra_table_code(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await extracao_vegetal("acai", ano=2023)
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["table_code"] == "289"

    async def test_fetch_sidra_classification_c193(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await extracao_vegetal("acai", ano=2023)
            call_kwargs = mock.call_args.kwargs
            assert "193" in call_kwargs["classifications"]
            assert call_kwargs["classifications"]["193"] == "3403"

    async def test_periodo_list(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await extracao_vegetal("acai", ano=[2021, 2022, 2023])
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "2021,2022,2023"

    async def test_uf_filter(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await extracao_vegetal("acai", ano=2023, uf="PA")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["ibge_territorial_code"] == "15"

    async def test_municipio_filter(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await extracao_vegetal("acai", ano=2023, uf="PA", nivel="municipio")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["territorial_level"] == "6"

    async def test_return_meta(self):
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            result = await extracao_vegetal("acai", ano=2023, return_meta=True)
            assert isinstance(result, tuple)
            df, meta = result
            assert isinstance(df, pd.DataFrame)
            assert meta.source == "ibge_extracao_vegetal"

    async def test_polars(self):
        pytest.importorskip("polars")
        from agrobr.ibge import extracao_vegetal

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await extracao_vegetal("acai", ano=2023, as_polars=True)
            import polars as pl

            assert isinstance(df, pl.DataFrame)

    async def test_lenha_unidade_metros_cubicos(self):
        from agrobr.ibge import extracao_vegetal

        mock_df = _build_mock_df(1)
        mock_df["D4C"] = "3434"
        mock_df["D4N"] = "Lenha"
        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = mock_df
            df = await extracao_vegetal("lenha", ano=2023)
            assert (df["unidade"] == "Metros cúbicos").all()


# ---------------------------------------------------------------------------
# Golden data
# ---------------------------------------------------------------------------


class TestExtracaoVegetalGoldenData:
    def test_golden_data_exists(self):
        assert GOLDEN_DIR.exists()
        assert (GOLDEN_DIR / "metadata.json").exists()
        assert (GOLDEN_DIR / "response.csv").exists()
        assert (GOLDEN_DIR / "expected.json").exists()

    def test_golden_metadata(self):
        meta = json.loads((GOLDEN_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert meta["source"] == "ibge"
        assert meta["query"]["table"] == "289"
        assert meta["query"]["classification_193"] == "3403"

    def test_golden_response_parseable(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) > 0
        assert "V" in df.columns

    def test_golden_parse_matches_expected(self):
        expected = json.loads((GOLDEN_DIR / "expected.json").read_text(encoding="utf-8"))
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        parsed = client.parse_sidra_response(
            df,
            rename_columns={
                "MC": "unidade_cod",
                "MN": "unidade_medida",
                "D1C": "localidade_cod",
                "D1N": "localidade",
                "D2C": "ano_cod",
                "D2N": "ano",
                "D3C": "variavel_cod",
                "D3N": "variavel_nome",
                "D4C": "produto_cod",
                "D4N": "produto_raw",
            },
        )
        assert len(parsed) == expected["count"]
        assert parsed["localidade"].iloc[0] == expected["first_row"]["ano"]

    def test_golden_all_values_positive(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        numeric_vals = pd.to_numeric(df["V"], errors="coerce").dropna()
        assert (numeric_vals > 0).all()


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


class TestExtracaoVegetalContract:
    def test_contract_registered(self):
        from agrobr.contracts import get_contract

        contract = get_contract("extrativismo_vegetal")
        assert contract is not None
        assert contract.name == "ibge.extracao_vegetal"

    def test_contract_validates_valid_df(self):
        from agrobr.contracts import validate_dataset

        df = pd.DataFrame(
            {
                "ano": [2023, 2023],
                "localidade": ["Pará", "Amazonas"],
                "localidade_cod": [15, 13],
                "produto": ["acai", "acai"],
                "valor": [1800000.0, 350000.0],
                "unidade": ["Toneladas", "Toneladas"],
                "fonte": ["ibge_extracao_vegetal", "ibge_extracao_vegetal"],
            }
        )
        validate_dataset(df, "extrativismo_vegetal")

    def test_contract_rejects_negative_values(self):
        from agrobr.contracts import validate_dataset
        from agrobr.exceptions import ContractViolationError

        df = pd.DataFrame(
            {
                "ano": [2023],
                "localidade": ["Test"],
                "localidade_cod": [15],
                "produto": ["acai"],
                "valor": [-100.0],
                "unidade": ["Toneladas"],
                "fonte": ["ibge_extracao_vegetal"],
            }
        )
        with pytest.raises(ContractViolationError):
            validate_dataset(df, "extrativismo_vegetal")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class TestExtracaoVegetalDataset:
    def test_dataset_registered(self):
        from agrobr.datasets.registry import list_datasets

        datasets = list_datasets()
        assert "extrativismo_vegetal" in datasets

    def test_dataset_info(self):
        from agrobr.datasets.extrativismo_vegetal import EXTRATIVISMO_VEGETAL_INFO

        assert EXTRATIVISMO_VEGETAL_INFO.name == "extrativismo_vegetal"
        assert EXTRATIVISMO_VEGETAL_INFO.update_frequency == "yearly"

    def test_dataset_products(self):
        from agrobr.datasets.extrativismo_vegetal import EXTRATIVISMO_VEGETAL_INFO

        assert len(EXTRATIVISMO_VEGETAL_INFO.products) == 12
        assert "acai" in EXTRATIVISMO_VEGETAL_INFO.products

    def test_dataset_sources(self):
        from agrobr.datasets.extrativismo_vegetal import EXTRATIVISMO_VEGETAL_INFO

        assert len(EXTRATIVISMO_VEGETAL_INFO.sources) == 1
        assert EXTRATIVISMO_VEGETAL_INFO.sources[0].name == "ibge_extracao_vegetal"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestExtracaoVegetalCachePolicy:
    def test_cache_policy_exists(self):
        from agrobr.cache.policies import POLICIES

        assert "ibge_extracao_vegetal" in POLICIES

    def test_cache_ttl_7_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_extracao_vegetal"]
        assert policy.ttl_seconds == 7 * 24 * 3600

    def test_cache_stale_90_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_extracao_vegetal"]
        assert policy.stale_max_seconds == 90 * 24 * 3600


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestProdutosExtracaoVegetalFunc:
    async def test_returns_list(self):
        from agrobr.ibge import produtos_extracao_vegetal

        result = await produtos_extracao_vegetal()
        assert isinstance(result, list)
        assert "acai" in result
        assert len(result) == 21


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestExtracaoVegetalIntegration:
    async def test_extracao_acai_real(self):
        from agrobr.ibge import extracao_vegetal

        df = await extracao_vegetal("acai", ano=2022, nivel="brasil")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "valor" in df.columns
