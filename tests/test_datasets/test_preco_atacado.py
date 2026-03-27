from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.preco_atacado import PRECO_ATACADO_INFO, PrecoAtacadoDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        {
            "data": [pd.Timestamp("2024-01-15")],
            "produto": ["TOMATE"],
            "categoria": ["HORTALICAS"],
            "unidade": ["KG"],
            "ceasa": ["CEAGESP - SAO PAULO"],
            "ceasa_uf": ["SP"],
            "preco": [5.50],
        }
    )


class TestPrecoAtacadoFetch:
    @pytest.mark.asyncio
    async def test_fetch_without_produto(self):
        dataset = PrecoAtacadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch()

        assert len(df) == 1
        assert "preco" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_with_produto(self):
        dataset = PrecoAtacadoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("TOMATE")

        args, _ = mock_fn.call_args
        assert args[0] == "TOMATE"

    @pytest.mark.asyncio
    async def test_fetch_with_ceasa(self):
        dataset = PrecoAtacadoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch(ceasa="CEAGESP")

        _, kwargs = mock_fn.call_args
        assert kwargs["ceasa"] == "CEAGESP"

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = PrecoAtacadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch(return_meta=True)

        assert meta.dataset == "preco_atacado"
        assert meta.contract_version == "1.0"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_contract_validation_called(self):
        dataset = PrecoAtacadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        with patch.object(dataset, "_validate_contract") as mock_validate:
            await dataset.fetch()
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = PrecoAtacadoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch()

    @pytest.mark.asyncio
    async def test_validate_produto_noop(self):
        dataset = PrecoAtacadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        await dataset.fetch("qualquer_produto_valido")


class TestPrecoAtacadoInfo:
    def test_products_empty(self):
        assert PRECO_ATACADO_INFO.products == []

    def test_license_zona_cinza(self):
        assert PRECO_ATACADO_INFO.license == "zona_cinza"


class TestPrecoAtacadoFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ceasa_forwards_params(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.conab.ceasa.precos",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.preco_atacado import _fetch_ceasa

            await _fetch_ceasa("TOMATE", ceasa="CEAGESP")
        mock_fn.assert_called_once_with(produto="TOMATE", ceasa="CEAGESP", return_meta=True)

    @pytest.mark.asyncio
    async def test_fetch_ceasa_defaults(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.conab.ceasa.precos",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.preco_atacado import _fetch_ceasa

            await _fetch_ceasa("")
        _, kwargs = mock_fn.call_args
        assert kwargs["produto"] is None
        assert kwargs["ceasa"] is None
