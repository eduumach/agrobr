from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.lista_suja import api
from agrobr.utils.warnings import warn_once_reset


def _make_xlsx() -> bytes:
    df = pd.DataFrame(
        {
            "EMPREGADOR": ["Fazenda X", "Empresa Y", "Sitio Z", "Rural W", "Agro V"],
            "CPF/CNPJ": [
                "12345678901",
                "98765432101",
                "11122233344",
                "55566677788",
                "99988877766",
            ],
            "ESTABELECIMENTO": ["Faz. X", "Emp. Y", "Sit. Z", "Rur. W", "Agr. V"],
            "UF": ["MT", "PA", "MA", "GO", "TO"],
            "MUNICÍPIO": ["Sinop", "Maraba", "Balsas", "Jatai", "Palmas"],
            "CNAE": ["0111", "0112", "0113", "0114", "0115"],
            "DATA DA INCLUSÃO": pd.to_datetime(
                ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"]
            ),
            "TRABALHADORES ENVOLVIDOS": [5, 12, 3, 8, 15],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


class TestEmpregadores:
    @pytest.fixture(autouse=True)
    def _reset_pii_warning(self):
        warn_once_reset("lista_suja_pii")
        yield
        warn_once_reset("lista_suja_pii")

    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        xlsx_data = _make_xlsx()
        with patch.object(
            api.client,
            "fetch_empregadores",
            new_callable=AsyncMock,
            return_value=(xlsx_data, "url"),
        ):
            df = await api.empregadores()
        assert len(df) == 5
        assert "empregador" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        xlsx_data = _make_xlsx()
        with patch.object(
            api.client,
            "fetch_empregadores",
            new_callable=AsyncMock,
            return_value=(xlsx_data, "url"),
        ):
            df, meta = await api.empregadores(return_meta=True)
        assert meta.source == "lista_suja"
        assert meta.source_method == "httpx+xlsx"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        xlsx_data = _make_xlsx()
        with patch.object(
            api.client,
            "fetch_empregadores",
            new_callable=AsyncMock,
            return_value=(xlsx_data, "url"),
        ):
            result = await api.empregadores(as_polars=True)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_uf_filter(self):
        xlsx_data = _make_xlsx()
        with patch.object(
            api.client,
            "fetch_empregadores",
            new_callable=AsyncMock,
            return_value=(xlsx_data, "url"),
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
        empty_df = pd.DataFrame(columns=["EMPREGADOR", "CPF/CNPJ", "UF"])
        buf = io.BytesIO()
        empty_df.to_excel(buf, index=False)
        empty_xlsx = buf.getvalue()
        with patch.object(
            api.client,
            "fetch_empregadores",
            new_callable=AsyncMock,
            return_value=(empty_xlsx, "url"),
        ):
            df = await api.empregadores()
        assert len(df) == 0

    @pytest.mark.asyncio
    async def test_pii_warning(self):
        xlsx_data = _make_xlsx()
        with (
            patch.object(
                api.client,
                "fetch_empregadores",
                new_callable=AsyncMock,
                return_value=(xlsx_data, "url"),
            ),
            pytest.warns(UserWarning, match="CPF/CNPJ"),
        ):
            await api.empregadores()
