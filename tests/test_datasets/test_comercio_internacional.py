from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.comercio_internacional import (
    COMERCIO_INTERNACIONAL_INFO,
    ComercioInternacionalDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _make_df(**overrides):
    row = {
        "periodo": "2024",
        "ano": 2024,
        "mes": float("nan"),
        "reporter_iso": "BRA",
        "reporter": "Brazil",
        "partner_iso": "CHN",
        "partner": "China",
        "fluxo_code": "X",
        "hs_code": "1201",
        "produto_desc": "Soybeans",
        "peso_liquido_kg": 50000000.0,
        "volume_ton": 50000.0,
        "valor_fob_usd": 25000000.0,
        "valor_cif_usd": float("nan"),
        "valor_primario_usd": 25000000.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestComercioInternacionalFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_df(self):
        dataset = ComercioInternacionalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "periodo" in df.columns
        assert "valor_fob_usd" in df.columns
        assert df.iloc[0]["reporter_iso"] == "BRA"

    @pytest.mark.asyncio
    async def test_params_passthrough(self):
        mock_fn = make_source(_make_df())
        dataset = ComercioInternacionalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            "soja",
            reporter="US",
            partner="CN",
            fluxo="M",
            periodo="2023",
            freq="M",
            api_key="test-key",
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["reporter"] == "US"
        assert call_kwargs["partner"] == "CN"
        assert call_kwargs["fluxo"] == "M"
        assert call_kwargs["periodo"] == "2023"
        assert call_kwargs["freq"] == "M"
        assert call_kwargs["api_key"] == "test-key"

    @pytest.mark.asyncio
    async def test_return_meta(self):
        dataset = ComercioInternacionalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "comercio_internacional"
        assert meta.contract_version == "1.0"
        assert "comtrade" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_snapshot_default_periodo(self):
        mock_fn = make_source(_make_df())
        dataset = ComercioInternacionalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        from agrobr.datasets.deterministic import deterministic

        async with deterministic("2023-06-15"):
            await dataset.fetch("soja")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["periodo"] == "2023"

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = ComercioInternacionalDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")


class TestComercioInternacionalValidation:
    def test_invalid_produto(self):
        dataset = ComercioInternacionalDataset()
        with pytest.raises(ValueError, match="banana_inexistente"):
            dataset._validate_produto("banana_inexistente")


class TestComercioInternacionalInfo:
    def test_source_comtrade(self):
        assert len(COMERCIO_INTERNACIONAL_INFO.sources) == 1
        assert COMERCIO_INTERNACIONAL_INFO.sources[0].name == "comtrade"

    def test_products_count(self):
        assert len(COMERCIO_INTERNACIONAL_INFO.products) == 17

    def test_license_livre(self):
        assert COMERCIO_INTERNACIONAL_INFO.license == "livre"


class TestComercioInternacionalFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_comtrade_forwards_params(self):
        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.comtrade.comercio", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.comercio_internacional import _fetch_comtrade

            await _fetch_comtrade(
                "soja",
                reporter="US",
                partner="BR",
                fluxo="M",
                periodo=2024,
                freq="M",
                api_key="key123",
            )
        mock_fn.assert_called_once_with(
            "soja",
            reporter="US",
            partner="BR",
            fluxo="M",
            periodo=2024,
            freq="M",
            api_key="key123",
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_comtrade_defaults(self):
        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.comtrade.comercio", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.comercio_internacional import _fetch_comtrade

            await _fetch_comtrade("soja")
        _, kwargs = mock_fn.call_args
        assert kwargs["reporter"] == "BR"
        assert kwargs["fluxo"] == "X"
        assert kwargs["freq"] == "A"
