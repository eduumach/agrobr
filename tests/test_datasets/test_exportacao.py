"""Testes específicos para o dataset exportacao (fetch com mock + prioridade)."""

from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.deterministic import deterministic
from agrobr.datasets.exportacao import EXPORTACAO_INFO, ExportacaoDataset, exportacao
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_export_df():
    return pd.DataFrame(
        [
            {
                "ano": 2024,
                "mes": 1,
                "produto": "soja",
                "uf": "MT",
                "kg_liquido": 5000000000,
                "valor_fob_usd": 2500000000,
            },
        ]
    )


class TestExportacaoSpecific:
    def test_info_comexstat_priority(self):
        comexstat = next(s for s in EXPORTACAO_INFO.sources if s.name == "comexstat")
        abiove = next(s for s in EXPORTACAO_INFO.sources if s.name == "abiove")
        assert comexstat.priority < abiove.priority


class TestExportacaoFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_export_df())
        df = await dataset.fetch("soja", ano=2024)

        assert len(df) == 1
        assert "kg_liquido" in df.columns
        assert df.iloc[0]["valor_fob_usd"] == 2500000000

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_export_df())
        df, meta = await dataset.fetch("soja", ano=2024, return_meta=True)

        assert meta.dataset == "exportacao"
        assert meta.contract_version == "1.0"
        assert "comexstat" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ExportacaoDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("banana")

    @pytest.mark.asyncio
    async def test_fetch_forwards_uf(self):
        dataset = ExportacaoDataset()
        mock_fn = make_source(_mock_export_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("soja", ano=2024, uf="MT")

        _, kwargs = mock_fn.call_args
        assert kwargs["uf"] == "MT"

    @pytest.mark.asyncio
    async def test_snapshot_sets_ano(self):
        dataset = ExportacaoDataset()
        mock_fn = make_source(_mock_export_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("soja")

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2024

    @pytest.mark.asyncio
    async def test_snapshot_does_not_override_explicit_ano(self):
        dataset = ExportacaoDataset()
        mock_fn = make_source(_mock_export_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("soja", ano=2023)

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2023


class TestExportacaoNormalize:
    @pytest.mark.asyncio
    async def test_normalize_adds_produto(self):
        df = _mock_export_df().drop(columns=["produto"])
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja", ano=2024)

        assert result["produto"].iloc[0] == "soja"

    @pytest.mark.asyncio
    async def test_normalize_keeps_existing_produto(self):
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_export_df())

        result = await dataset.fetch("soja", ano=2024)

        assert result["produto"].iloc[0] == "soja"


class TestExportacaoFallback:
    @pytest.mark.asyncio
    async def test_comexstat_fails_falls_back_to_abiove(self):
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))
        dataset.info.sources[1].fetch_fn = make_source(_mock_export_df())

        df, meta = await dataset.fetch("soja", ano=2024, return_meta=True)

        assert len(df) == 1
        assert meta.attempted_sources == ["comexstat", "abiove"]
        assert meta.selected_source == "abiove"

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        dataset = ExportacaoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))
        dataset.info.sources[1].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja", ano=2024)


class TestExportacaoPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        with patch.object(ExportacaoDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _mock_export_df()
            await exportacao("soja", ano=2024, uf="MT")

            mock_fetch.assert_called_once_with("soja", ano=2024, uf="MT", return_meta=False)

    @pytest.mark.asyncio
    async def test_public_function_return_meta(self):
        with patch.object(ExportacaoDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (_mock_export_df(), mock_source_meta())
            result = await exportacao("soja", ano=2024, return_meta=True)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], pd.DataFrame)


class TestExportacaoFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_comexstat_forwards_params(self):
        meta = mock_source_meta()
        with patch(
            "agrobr.comexstat.exportacao",
            new_callable=AsyncMock,
            return_value=(_mock_export_df(), meta),
        ) as mock_fn:
            from agrobr.datasets.exportacao import _fetch_comexstat

            await _fetch_comexstat("soja", ano=2024, uf="PR")
        mock_fn.assert_called_once_with("soja", ano=2024, uf="PR", return_meta=True)

    @pytest.mark.asyncio
    async def test_fetch_abiove_column_transform(self):
        df = pd.DataFrame({"volume_ton": [100.0], "receita_usd_mil": [50.0]})
        meta = mock_source_meta()
        with patch("agrobr.abiove.exportacao", new_callable=AsyncMock, return_value=(df, meta)):
            from agrobr.datasets.exportacao import _fetch_abiove

            result_df, _ = await _fetch_abiove("soja", ano=2024)
        assert result_df["kg_liquido"].iloc[0] == 100000.0
        assert result_df["valor_fob_usd"].iloc[0] == 50000.0

    @pytest.mark.asyncio
    async def test_fetch_abiove_skip_transform_if_cols_exist(self):
        df = pd.DataFrame(
            {
                "volume_ton": [100.0],
                "kg_liquido": [999.0],
                "receita_usd_mil": [50.0],
                "valor_fob_usd": [888.0],
            }
        )
        meta = mock_source_meta()
        with patch("agrobr.abiove.exportacao", new_callable=AsyncMock, return_value=(df, meta)):
            from agrobr.datasets.exportacao import _fetch_abiove

            result_df, _ = await _fetch_abiove("soja", ano=2024)
        assert result_df["kg_liquido"].iloc[0] == 999.0
        assert result_df["valor_fob_usd"].iloc[0] == 888.0
