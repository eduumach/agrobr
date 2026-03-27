from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.zoneamento_agricola import (
    ZONEAMENTO_AGRICOLA_INFO,
    ZoneamentoAgricolaDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_df(**overrides):
    row = {
        "cultura": "SOJA",
        "safra": "2024/2025",
        "geocodigo": "5103403",
        "uf": "MT",
        "municipio": "Cuiabá",
        "solo_codigo": 2,
        "ciclo_codigo": 1,
        "clima": None,
        "manejo": None,
        "portaria": "Portaria 123/2024",
        **{f"dec{i}": 0 for i in range(1, 37)},
    }
    row["dec10"] = 3
    row["dec11"] = 4
    row["dec12"] = 5
    row.update(overrides)
    return pd.DataFrame([row])


class TestZoneamentoAgricolaFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_df(self):
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch(cultura="SOJA", uf="MT")

        assert len(df) == 1
        assert "cultura" in df.columns
        assert "geocodigo" in df.columns
        assert "dec1" in df.columns
        assert "dec36" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_with_filters(self):
        mock_fn = make_source(_make_df())
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            cultura="SOJA",
            uf="MT",
            municipio=5103403,
            safra="2024/2025",
            solo=2,
            ciclo=1,
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["cultura"] == "SOJA"
        assert call_kwargs["uf"] == "MT"
        assert call_kwargs["municipio"] == 5103403
        assert call_kwargs["safra"] == "2024/2025"
        assert call_kwargs["solo"] == 2
        assert call_kwargs["ciclo"] == 1

    @pytest.mark.asyncio
    async def test_return_meta(self):
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch(cultura="SOJA", return_meta=True)

        assert meta.dataset == "zoneamento_agricola"
        assert meta.contract_version == "1.0"
        assert "zarc" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_no_params(self):
        mock_fn = make_source(_make_df())
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        df = await dataset.fetch()

        assert len(df) == 1

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch(cultura="SOJA")


class TestZoneamentoAgricolaInfo:
    def test_source_zarc(self):
        assert len(ZONEAMENTO_AGRICOLA_INFO.sources) == 1
        assert ZONEAMENTO_AGRICOLA_INFO.sources[0].name == "zarc"

    def test_products_empty(self):
        assert ZONEAMENTO_AGRICOLA_INFO.products == []

    def test_license_livre(self):
        assert ZONEAMENTO_AGRICOLA_INFO.license == "livre"


class TestZoneamentoAgricolaContract:
    @pytest.mark.asyncio
    async def test_contract_validation_called(self):
        dataset = ZoneamentoAgricolaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())

        with patch.object(dataset, "_validate_contract") as mock_validate:
            await dataset.fetch(cultura="SOJA")
            mock_validate.assert_called_once()

    def test_dec_columns_present(self):
        df = _make_df()
        dec_cols = [c for c in df.columns if c.startswith("dec")]
        assert len(dec_cols) == 36
        assert "dec1" in dec_cols
        assert "dec36" in dec_cols


class TestZoneamentoAgricolaFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_zarc_forwards_params(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.zarc.zoneamento",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.zoneamento_agricola import _fetch_zarc

            await _fetch_zarc(
                "",
                cultura="SOJA",
                uf="MT",
                municipio=5103403,
                safra="2024/2025",
                solo=2,
                ciclo=1,
            )
        mock_fn.assert_called_once_with(
            cultura="SOJA",
            uf="MT",
            municipio=5103403,
            safra="2024/2025",
            solo=2,
            ciclo=1,
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_zarc_defaults(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.zarc.zoneamento",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.zoneamento_agricola import _fetch_zarc

            await _fetch_zarc("")
        _, kwargs = mock_fn.call_args
        assert kwargs["cultura"] is None
        assert kwargs["uf"] is None
        assert kwargs["municipio"] is None
        assert kwargs["safra"] is None
        assert kwargs["solo"] is None
        assert kwargs["ciclo"] is None
