from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.lista_suja import api
from agrobr.utils.warnings import warn_once_reset


def _mock_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "empregador": ["Fazenda X", "Empresa Y", "Sitio Z", "Rural W", "Agro V"],
            "cpf_cnpj": ["12345678901", "98765432101", "11122233344", "55566677788", "99988877766"],
            "estabelecimento": ["Faz. X", "Emp. Y", "Sit. Z", "Rur. W", "Agr. V"],
            "uf": ["MT", "PA", "MA", "GO", "TO"],
            "cnae": ["0111", "0112", "0113", "0114", "0115"],
            "data_inclusao": pd.to_datetime(
                ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"]
            ),
            "trabalhadores_resgatados": [5, 12, 3, 8, 15],
            "ano_acao_fiscal": [2023, 2023, 2023, 2023, 2023],
        }
    )


class TestEmpregadores:
    @pytest.fixture(autouse=True)
    def _reset_pii_warning(self):
        warn_once_reset("lista_suja_pii")
        yield
        warn_once_reset("lista_suja_pii")

    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=_mock_df()),
        ):
            df = await api.empregadores()
        assert len(df) == 5
        assert "empregador" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=_mock_df()),
        ):
            df, meta = await api.empregadores(return_meta=True)
        assert meta.source == "lista_suja"
        assert meta.source_method == "httpx+pdf"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=_mock_df()),
        ):
            result = await api.empregadores(as_polars=True)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_uf_filter(self):
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=_mock_df()),
        ):
            df = await api.empregadores(uf="MT")
        assert all(df["uf"] == "MT")
        assert len(df) == 1

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.empregadores(uf="INVALID")

    @pytest.mark.asyncio
    async def test_empty_result(self):
        from agrobr.lista_suja.models import COLUNAS_SAIDA

        empty = pd.DataFrame(columns=COLUNAS_SAIDA)
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=empty),
        ):
            df = await api.empregadores()
        assert len(df) == 0

    @pytest.mark.asyncio
    async def test_pii_warning(self):
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(b"pdf", "url"),
            ),
            patch.object(api.parser, "parse_empregadores", return_value=_mock_df()),
            pytest.warns(UserWarning, match="CPF/CNPJ"),
        ):
            await api.empregadores()
