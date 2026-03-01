from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibge import client

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ibge" / "leite_trimestral_sample"


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


class TestConstantesLeite:
    def test_tabela_leite_trimestral(self):
        assert client.TABELAS_LEITE["leite_trimestral"] == "1086"

    def test_variavel_leite_adquirido(self):
        assert client.VARIAVEIS_LEITE["leite_adquirido"] == "282"

    def test_variavel_leite_industrializado(self):
        assert client.VARIAVEIS_LEITE["leite_industrializado"] == "283"

    def test_variavel_preco_medio(self):
        assert client.VARIAVEIS_LEITE["preco_medio"] == "2522"

    def test_codes_numeric(self):
        for name, code in client.VARIAVEIS_LEITE.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _build_mock_df(n_ufs=3):
    rows = []
    ufs = [("31", "Minas Gerais"), ("43", "Rio Grande do Sul"), ("41", "Paraná")][:n_ufs]
    vars_ = [
        ("282", "Leite cru adquirido"),
        ("283", "Leite cru industrializado"),
        ("2522", "Preço médio pago ao produtor"),
    ]
    for cod, nome in ufs:
        for var_cod, var_nome in vars_:
            value = "2.45" if var_cod == "2522" else str(800000 + int(cod) * 10000)
            rows.append(
                {
                    "D1C": cod,
                    "D1N": nome,
                    "D2C": "202503",
                    "D2N": "3º trimestre 2025",
                    "D3C": var_cod,
                    "D3N": var_nome,
                    "V": value,
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1028" if var_cod != "2522" else "1",
                    "MN": "Mil litros" if var_cod != "2522" else "Reais por litro",
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mocked
# ---------------------------------------------------------------------------


class TestLeiteMocked:
    async def test_returns_dataframe(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    async def test_pivot_wide(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            assert "leite_adquirido" in df.columns
            assert "leite_industrializado" in df.columns
            assert "preco_medio" in df.columns

    async def test_columns_after_pivot(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            expected = [
                "trimestre",
                "localidade",
                "localidade_cod",
                "leite_adquirido",
                "leite_industrializado",
                "preco_medio",
                "fonte",
            ]
            assert list(df.columns) == expected

    async def test_trimestre_format(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            assert (df["trimestre"] == "202503").all()

    async def test_uf_filter(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await leite_trimestral(trimestre="202503", uf="MG")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["ibge_territorial_code"] == "31"

    async def test_list_of_trimestres(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await leite_trimestral(trimestre=["202501", "202502", "202503"])
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "202501,202502,202503"

    async def test_no_trimestre_uses_last(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await leite_trimestral()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "last"

    async def test_return_meta(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            result = await leite_trimestral(trimestre="202503", return_meta=True)
            assert isinstance(result, tuple)
            df, meta = result
            assert isinstance(df, pd.DataFrame)
            assert meta.source == "ibge_leite_trimestral"

    async def test_polars(self):
        pytest.importorskip("polars")
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503", as_polars=True)
            import polars as pl

            assert isinstance(df, pl.DataFrame)

    async def test_preco_medio_numeric(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            assert pd.api.types.is_numeric_dtype(df["preco_medio"])

    async def test_fonte(self):
        from agrobr.ibge import leite_trimestral

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await leite_trimestral(trimestre="202503")
            assert (df["fonte"] == "ibge_leite_trimestral").all()


# ---------------------------------------------------------------------------
# Golden data
# ---------------------------------------------------------------------------


class TestLeiteGoldenData:
    def test_golden_data_exists(self):
        assert GOLDEN_DIR.exists()
        assert (GOLDEN_DIR / "metadata.json").exists()
        assert (GOLDEN_DIR / "response.csv").exists()
        assert (GOLDEN_DIR / "expected.json").exists()

    def test_golden_metadata(self):
        meta = json.loads((GOLDEN_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert meta["source"] == "ibge"
        assert meta["query"]["table"] == "1086"

    def test_golden_response_parseable(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) > 0
        assert "V" in df.columns
        assert "D3C" in df.columns

    def test_golden_has_3_variables(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        var_codes = df["D3C"].unique()
        assert set(var_codes) == {"282", "283", "2522"}


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


class TestLeiteContract:
    def test_contract_registered(self):
        from agrobr.contracts import get_contract

        contract = get_contract("leite_industrial")
        assert contract is not None
        assert contract.name == "ibge.leite_trimestral"

    def test_contract_validates_valid_df(self):
        from agrobr.contracts import validate_dataset

        df = pd.DataFrame(
            {
                "trimestre": ["202503"],
                "localidade": ["Minas Gerais"],
                "localidade_cod": [31],
                "leite_adquirido": [1850000.0],
                "leite_industrializado": [1620000.0],
                "preco_medio": [2.45],
                "fonte": ["ibge_leite_trimestral"],
            }
        )
        validate_dataset(df, "leite_industrial")

    def test_contract_rejects_negative_values(self):
        from agrobr.contracts import validate_dataset
        from agrobr.exceptions import ContractViolationError

        df = pd.DataFrame(
            {
                "trimestre": ["202503"],
                "localidade": ["Test"],
                "localidade_cod": [31],
                "leite_adquirido": [-100.0],
                "leite_industrializado": [1000.0],
                "preco_medio": [2.0],
                "fonte": ["ibge_leite_trimestral"],
            }
        )
        with pytest.raises(ContractViolationError):
            validate_dataset(df, "leite_industrial")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class TestLeiteDataset:
    def test_dataset_registered(self):
        from agrobr.datasets.registry import list_datasets

        datasets = list_datasets()
        assert "leite_industrial" in datasets

    def test_dataset_info(self):
        from agrobr.datasets.leite_industrial import LEITE_INDUSTRIAL_INFO

        assert LEITE_INDUSTRIAL_INFO.name == "leite_industrial"
        assert LEITE_INDUSTRIAL_INFO.update_frequency == "quarterly"

    def test_dataset_products(self):
        from agrobr.datasets.leite_industrial import LEITE_INDUSTRIAL_INFO

        assert LEITE_INDUSTRIAL_INFO.products == ["leite"]

    def test_dataset_sources(self):
        from agrobr.datasets.leite_industrial import LEITE_INDUSTRIAL_INFO

        assert len(LEITE_INDUSTRIAL_INFO.sources) == 1
        assert LEITE_INDUSTRIAL_INFO.sources[0].name == "ibge_leite_trimestral"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestLeiteCachePolicy:
    def test_cache_policy_exists(self):
        from agrobr.cache.policies import POLICIES

        assert "ibge_leite_trimestral" in POLICIES

    def test_cache_ttl_7_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_leite_trimestral"]
        assert policy.ttl_seconds == 7 * 24 * 3600

    def test_cache_stale_90_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_leite_trimestral"]
        assert policy.stale_max_seconds == 90 * 24 * 3600


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestLeiteIntegration:
    async def test_leite_trimestral_real(self):
        from agrobr.ibge import leite_trimestral

        df = await leite_trimestral(trimestre="202303")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "leite_adquirido" in df.columns
