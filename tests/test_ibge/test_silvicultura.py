from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibge import client

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ibge" / "silvicultura_sample"


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


class TestTabelasPEVS:
    def test_tabela_silvicultura_producao(self):
        assert client.TABELAS_PEVS["silvicultura_producao"] == "291"

    def test_tabela_silvicultura_area(self):
        assert client.TABELAS_PEVS["silvicultura_area"] == "5930"

    def test_tabela_extracao_vegetal(self):
        assert client.TABELAS_PEVS["extracao_vegetal"] == "289"

    def test_all_codes_numeric(self):
        for name, code in client.TABELAS_PEVS.items():
            assert code.isdigit(), f"{name} has non-numeric code: {code}"


class TestVariaveisSilvicultura:
    def test_quantidade_produzida(self):
        assert client.VARIAVEIS_SILVICULTURA["quantidade_produzida"] == "142"

    def test_valor_producao(self):
        assert client.VARIAVEIS_SILVICULTURA["valor_producao"] == "143"

    def test_codes_numeric(self):
        for name, code in client.VARIAVEIS_SILVICULTURA.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


class TestVariaveisSilviculturaArea:
    def test_area_total(self):
        assert client.VARIAVEIS_SILVICULTURA_AREA["area_total"] == "6549"


class TestProdutosSilvicultura:
    def test_contains_carvao(self):
        assert "carvao" in client.PRODUTOS_SILVICULTURA
        assert client.PRODUTOS_SILVICULTURA["carvao"] == "3455"

    def test_contains_lenha(self):
        assert "lenha" in client.PRODUTOS_SILVICULTURA

    def test_contains_madeira_tora(self):
        assert "madeira_tora" in client.PRODUTOS_SILVICULTURA

    def test_has_14_products(self):
        assert len(client.PRODUTOS_SILVICULTURA) == 14

    def test_all_codes_numeric(self):
        for name, code in client.PRODUTOS_SILVICULTURA.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


class TestEspeciesSilviculturaArea:
    def test_eucalipto(self):
        assert client.ESPECIES_SILVICULTURA_AREA["eucalipto"] == "39326"

    def test_pinus(self):
        assert client.ESPECIES_SILVICULTURA_AREA["pinus"] == "39327"

    def test_outras(self):
        assert client.ESPECIES_SILVICULTURA_AREA["outras"] == "39328"

    def test_has_3_species(self):
        assert len(client.ESPECIES_SILVICULTURA_AREA) == 3


class TestUnidadesSilvicultura:
    def test_carvao_toneladas(self):
        assert client.UNIDADES_SILVICULTURA["carvao"] == "Toneladas"

    def test_lenha_metros_cubicos(self):
        assert client.UNIDADES_SILVICULTURA["lenha"] == "Metros cúbicos"

    def test_madeira_tora_metros_cubicos(self):
        assert client.UNIDADES_SILVICULTURA["madeira_tora"] == "Metros cúbicos"

    def test_all_products_have_unit(self):
        for prod in client.PRODUTOS_SILVICULTURA:
            assert prod in client.UNIDADES_SILVICULTURA, (
                f"{prod} missing from UNIDADES_SILVICULTURA"
            )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestSilviculturaValidation:
    async def test_produto_invalido(self):
        from agrobr.ibge import silvicultura

        with pytest.raises(ValueError, match="Produto não suportado"):
            await silvicultura("banana_inexistente")

    async def test_variavel_invalida(self):
        from agrobr.ibge import silvicultura

        with pytest.raises(ValueError, match="Variável não suportada"):
            await silvicultura("carvao", variavel="peso")

    async def test_especie_invalida_para_area(self):
        from agrobr.ibge import silvicultura

        with pytest.raises(ValueError, match="Espécie não suportada para área"):
            await silvicultura("carvao", variavel="area")


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _build_mock_df(n_ufs=3):
    rows = []
    ufs = [("31", "Minas Gerais"), ("35", "São Paulo"), ("51", "Mato Grosso do Sul")][:n_ufs]
    for cod, nome in ufs:
        rows.append(
            {
                "D1C": cod,
                "D1N": nome,
                "D2C": "2023",
                "D2N": "2023",
                "D3C": "142",
                "D3N": "Quantidade produzida na silvicultura",
                "D4C": "3455",
                "D4N": "Carvão vegetal",
                "V": str(1000000 + int(cod) * 10000),
                "NC": "3",
                "NN": "Unidade da Federação",
                "MC": "23",
                "MN": "Toneladas",
            }
        )
    return pd.DataFrame(rows)


def _build_mock_area_df(n_ufs=3):
    rows = []
    ufs = [("31", "Minas Gerais"), ("35", "São Paulo"), ("41", "Paraná")][:n_ufs]
    for cod, nome in ufs:
        rows.append(
            {
                "D1C": cod,
                "D1N": nome,
                "D2C": "2023",
                "D2N": "2023",
                "D3C": "6549",
                "D3N": "Área total existente em 31/12 dos efetivos da silvicultura",
                "D4C": "39326",
                "D4N": "Eucalipto",
                "V": str(500000 + int(cod) * 1000),
                "NC": "3",
                "NN": "Unidade da Federação",
                "MC": "30",
                "MN": "Hectares",
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mocked
# ---------------------------------------------------------------------------


class TestSilviculturaMocked:
    async def test_returns_dataframe(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    async def test_output_columns(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023)
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
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023)
            assert (df["produto"] == "carvao").all()

    async def test_unidade(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023)
            assert (df["unidade"] == "Toneladas").all()

    async def test_fonte(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023)
            assert (df["fonte"] == "ibge_silvicultura").all()

    async def test_fetch_sidra_table_code_producao(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await silvicultura("carvao", ano=2023)
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["table_code"] == "291"

    async def test_fetch_sidra_table_code_area(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_area_df()
            await silvicultura("eucalipto", ano=2023, variavel="area")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["table_code"] == "5930"

    async def test_fetch_sidra_classification_c194(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await silvicultura("carvao", ano=2023)
            call_kwargs = mock.call_args.kwargs
            assert "194" in call_kwargs["classifications"]
            assert call_kwargs["classifications"]["194"] == "3455"

    async def test_fetch_sidra_classification_c734(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_area_df()
            await silvicultura("eucalipto", ano=2023, variavel="area")
            call_kwargs = mock.call_args.kwargs
            assert "734" in call_kwargs["classifications"]
            assert call_kwargs["classifications"]["734"] == "39326"

    async def test_periodo_list(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await silvicultura("carvao", ano=[2021, 2022, 2023])
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "2021,2022,2023"

    async def test_uf_filter(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await silvicultura("carvao", ano=2023, uf="MG")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["ibge_territorial_code"] == "31"

    async def test_municipio_filter(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await silvicultura("carvao", ano=2023, uf="MG", nivel="municipio")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["territorial_level"] == "6"
            assert call_kwargs["ibge_territorial_code"] == "in N3 31"

    async def test_return_meta(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            result = await silvicultura("carvao", ano=2023, return_meta=True)
            assert isinstance(result, tuple)
            df, meta = result
            assert isinstance(df, pd.DataFrame)
            assert meta.source == "ibge_silvicultura"

    async def test_polars(self):
        pytest.importorskip("polars")
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await silvicultura("carvao", ano=2023, as_polars=True)
            import polars as pl

            assert isinstance(df, pl.DataFrame)

    async def test_variavel_area(self):
        from agrobr.ibge import silvicultura

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_area_df()
            df = await silvicultura("eucalipto", ano=2023, variavel="area")
            assert isinstance(df, pd.DataFrame)
            assert (df["unidade"] == "Hectares").all()
            assert (df["produto"] == "eucalipto").all()


# ---------------------------------------------------------------------------
# Golden data
# ---------------------------------------------------------------------------


class TestSilviculturaGoldenData:
    def test_golden_data_exists(self):
        assert GOLDEN_DIR.exists()
        assert (GOLDEN_DIR / "metadata.json").exists()
        assert (GOLDEN_DIR / "response.csv").exists()
        assert (GOLDEN_DIR / "expected.json").exists()

    def test_golden_metadata(self):
        meta = json.loads((GOLDEN_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert meta["source"] == "ibge"
        assert meta["query"]["table"] == "291"
        assert meta["query"]["classification_194"] == "3455"

    def test_golden_response_parseable(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) > 0
        assert "V" in df.columns
        assert "D1N" in df.columns

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
        assert parsed["valor"].iloc[0] == expected["first_row"]["valor"]

    def test_golden_all_values_positive(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        numeric_vals = pd.to_numeric(df["V"], errors="coerce").dropna()
        assert (numeric_vals > 0).all()


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


class TestSilviculturaContract:
    def test_contract_registered(self):
        from agrobr.contracts import get_contract

        contract = get_contract("silvicultura")
        assert contract is not None
        assert contract.name == "ibge.silvicultura"

    def test_contract_validates_valid_df(self):
        from agrobr.contracts import validate_dataset

        df = pd.DataFrame(
            {
                "ano": [2023, 2023],
                "localidade": ["Minas Gerais", "São Paulo"],
                "localidade_cod": [31, 35],
                "produto": ["carvao", "carvao"],
                "valor": [1250000.0, 980000.0],
                "unidade": ["Toneladas", "Toneladas"],
                "fonte": ["ibge_silvicultura", "ibge_silvicultura"],
            }
        )
        validate_dataset(df, "silvicultura")

    def test_contract_rejects_negative_values(self):
        from agrobr.contracts import validate_dataset
        from agrobr.exceptions import ContractViolationError

        df = pd.DataFrame(
            {
                "ano": [2023],
                "localidade": ["Test"],
                "localidade_cod": [31],
                "produto": ["carvao"],
                "valor": [-100.0],
                "unidade": ["Toneladas"],
                "fonte": ["ibge_silvicultura"],
            }
        )
        with pytest.raises(ContractViolationError):
            validate_dataset(df, "silvicultura")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class TestSilviculturaDataset:
    def test_dataset_registered(self):
        from agrobr.datasets.registry import list_datasets

        datasets = list_datasets()
        assert "silvicultura" in datasets

    def test_dataset_info(self):
        from agrobr.datasets.silvicultura import SILVICULTURA_INFO

        assert SILVICULTURA_INFO.name == "silvicultura"
        assert SILVICULTURA_INFO.update_frequency == "yearly"

    def test_dataset_products(self):
        from agrobr.datasets.silvicultura import SILVICULTURA_INFO

        assert len(SILVICULTURA_INFO.products) == 8
        assert "carvao" in SILVICULTURA_INFO.products

    def test_dataset_sources(self):
        from agrobr.datasets.silvicultura import SILVICULTURA_INFO

        assert len(SILVICULTURA_INFO.sources) == 1
        assert SILVICULTURA_INFO.sources[0].name == "ibge_silvicultura"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestSilviculturaCachePolicy:
    def test_cache_policy_exists(self):
        from agrobr.cache.policies import POLICIES

        assert "ibge_silvicultura" in POLICIES

    def test_cache_ttl_7_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_silvicultura"]
        assert policy.ttl_seconds == 7 * 24 * 3600

    def test_cache_stale_90_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_silvicultura"]
        assert policy.stale_max_seconds == 90 * 24 * 3600


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestProdutosSilviculturaFunc:
    async def test_returns_list(self):
        from agrobr.ibge import produtos_silvicultura

        result = await produtos_silvicultura()
        assert isinstance(result, list)
        assert "carvao" in result
        assert len(result) == 14


class TestEspeciesSilviculturaAreaFunc:
    async def test_returns_list(self):
        from agrobr.ibge import especies_silvicultura_area

        result = await especies_silvicultura_area()
        assert isinstance(result, list)
        assert "eucalipto" in result
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSilviculturaIntegration:
    async def test_silvicultura_carvao_real(self):
        from agrobr.ibge import silvicultura

        df = await silvicultura("carvao", ano=2022, nivel="brasil")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "valor" in df.columns
