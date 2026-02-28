from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibge import client

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ibge" / "pib_agro_sample"


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


class TestConstantesPib:
    def test_tabela_pib_corrente(self):
        assert client.TABELAS_PIB["pib_corrente"] == "1846"

    def test_tabela_pib_real(self):
        assert client.TABELAS_PIB["pib_real"] == "6612"

    def test_variavel_corrente(self):
        assert client.VARIAVEIS_PIB["corrente"] == "585"

    def test_variavel_real_1995(self):
        assert client.VARIAVEIS_PIB["real_1995"] == "9318"

    def test_setor_agropecuaria(self):
        assert client.SETORES_PIB["agropecuaria"] == "90687"

    def test_setor_industria(self):
        assert client.SETORES_PIB["industria"] == "90691"

    def test_setor_servicos(self):
        assert client.SETORES_PIB["servicos"] == "90696"

    def test_setor_pib_total(self):
        assert client.SETORES_PIB["pib_total"] == "90707"

    def test_has_4_setores(self):
        assert len(client.SETORES_PIB) == 4

    def test_all_codes_numeric(self):
        for name, code in client.SETORES_PIB.items():
            assert code.isdigit(), f"{name}: {code} not numeric"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestPibValidation:
    async def test_setor_invalido(self):
        from agrobr.ibge.api import pib_agro

        with pytest.raises(ValueError, match="Setor não suportado"):
            await pib_agro(setor="energia")

    async def test_precos_invalido(self):
        from agrobr.ibge.api import pib_agro

        with pytest.raises(ValueError, match="Tipo de preços não suportado"):
            await pib_agro(precos="constante_2020")


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _build_mock_df(n_trimestres=4):
    rows = []
    trimestres = [
        ("202501", "1º trimestre 2025"),
        ("202502", "2º trimestre 2025"),
        ("202503", "3º trimestre 2025"),
        ("202504", "4º trimestre 2025"),
    ][:n_trimestres]
    for cod, nome in trimestres:
        rows.append(
            {
                "D1C": "1",
                "D1N": "Brasil",
                "D2C": cod,
                "D2N": nome,
                "D3C": "585",
                "D3N": "Valores a preços correntes",
                "D4C": "90687",
                "D4N": "Agropecuária - total",
                "V": str(125000 + int(cod[-2:]) * 5000),
                "NC": "1",
                "NN": "Brasil",
                "MC": "63",
                "MN": "Milhões de Reais",
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mocked
# ---------------------------------------------------------------------------


class TestPibMocked:
    async def test_returns_dataframe(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await pib_agro(trimestre="202501")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    async def test_table_corrente(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await pib_agro(precos="corrente")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["table_code"] == "1846"

    async def test_table_real(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await pib_agro(precos="real_1995")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["table_code"] == "6612"

    async def test_setor_classification(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df(1)
            await pib_agro(setor="agropecuaria")
            call_kwargs = mock.call_args.kwargs
            assert "11255" in call_kwargs["classifications"]
            assert call_kwargs["classifications"]["11255"] == "90687"

    async def test_output_columns(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await pib_agro()
            expected = ["trimestre", "valor", "unidade", "setor", "fonte"]
            assert list(df.columns) == expected

    async def test_fonte(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await pib_agro()
            assert (df["fonte"] == "ibge_pib").all()

    async def test_setor_column(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await pib_agro(setor="industria")
            assert (df["setor"] == "industria").all()

    async def test_return_meta(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            result = await pib_agro(return_meta=True)
            assert isinstance(result, tuple)
            df, meta = result
            assert isinstance(df, pd.DataFrame)
            assert meta.source == "ibge_pib"

    async def test_polars(self):
        pytest.importorskip("polars")
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            df = await pib_agro(as_polars=True)
            import polars as pl

            assert isinstance(df, pl.DataFrame)

    async def test_list_of_trimestres(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await pib_agro(trimestre=["202501", "202502"])
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "202501,202502"

    async def test_no_trimestre_uses_last(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await pib_agro()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["period"] == "last"

    async def test_brasil_level(self):
        from agrobr.ibge.api import pib_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_df()
            await pib_agro()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["territorial_level"] == "1"


# ---------------------------------------------------------------------------
# Golden data
# ---------------------------------------------------------------------------


class TestPibGoldenData:
    def test_golden_data_exists(self):
        assert GOLDEN_DIR.exists()
        assert (GOLDEN_DIR / "metadata.json").exists()
        assert (GOLDEN_DIR / "response.csv").exists()
        assert (GOLDEN_DIR / "expected.json").exists()

    def test_golden_metadata(self):
        meta = json.loads((GOLDEN_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert meta["source"] == "ibge"
        assert meta["query"]["table"] == "1846"
        assert meta["query"]["classification_11255"] == "90687"

    def test_golden_response_parseable(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) > 0
        assert "V" in df.columns

    def test_golden_all_values_positive(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        numeric_vals = pd.to_numeric(df["V"], errors="coerce").dropna()
        assert (numeric_vals > 0).all()


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestPibCachePolicy:
    def test_cache_policy_exists(self):
        from agrobr.cache.policies import POLICIES

        assert "ibge_pib" in POLICIES

    def test_cache_ttl_7_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_pib"]
        assert policy.ttl_seconds == 7 * 24 * 3600

    def test_cache_stale_90_days(self):
        from agrobr.cache.policies import POLICIES

        policy = POLICIES["ibge_pib"]
        assert policy.stale_max_seconds == 90 * 24 * 3600


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPibIntegration:
    async def test_pib_agro_corrente_real(self):
        from agrobr.ibge.api import pib_agro

        df = await pib_agro(precos="corrente")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "valor" in df.columns
