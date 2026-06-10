import httpx
import pandas as pd
import pytest

from agrobr.datasets.movimentacao_portuaria import (
    MOVIMENTACAO_PORTUARIA_INFO,
    MovimentacaoPortuariaDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_df(**overrides):
    row = {
        "ano": 2024,
        "mes": 6,
        "data_atracacao": "2024-06-15",
        "tipo_navegacao": "Longo Curso",
        "tipo_operacao": "Embarque",
        "natureza_carga": "Granel Sólido",
        "sentido": "Embarcados",
        "porto": "Santos",
        "complexo_portuario": "Santos",
        "terminal": "Terminal de Granéis",
        "municipio": "Santos",
        "uf": "SP",
        "regiao": "Sudeste",
        "cd_mercadoria": "1201",
        "mercadoria": "Soja",
        "grupo_mercadoria": "Grãos",
        "origem": "Brasil",
        "destino": "China",
        "peso_bruto_ton": 65000.0,
        "qt_carga": 64500.0,
        "teu": 0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestMovimentacaoPortuariaAgregacao:
    @pytest.mark.asyncio
    async def test_agrega_por_pk_do_contrato(self):
        df_detalhe = pd.concat(
            [
                _make_df(peso_bruto_ton=60000.0, qt_carga=59000.0, teu=2),
                _make_df(peso_bruto_ton=5000.0, qt_carga=5500.0, teu=1, terminal="Outro Terminal"),
            ],
            ignore_index=True,
        )
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = make_source(df_detalhe)

        df = await dataset.fetch(ano=2024)

        assert len(df) == 1
        assert df["peso_bruto_ton"].iloc[0] == 65000.0
        assert df["qt_carga"].iloc[0] == 64500.0
        assert df["teu"].iloc[0] == 3

    @pytest.mark.asyncio
    async def test_detalhe_unico_preservado_misto_vira_none(self):
        df_detalhe = pd.concat(
            [
                _make_df(terminal="Terminal A", origem="Brasil"),
                _make_df(terminal="Terminal B", origem="Brasil"),
            ],
            ignore_index=True,
        )
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = make_source(df_detalhe)

        df = await dataset.fetch(ano=2024)

        assert len(df) == 1
        assert df["origem"].iloc[0] == "Brasil"
        assert df["terminal"].iloc[0] is None
        assert "data_atracacao" in df.columns
        assert "natureza_carga" in df.columns


class TestMovimentacaoPortuariaFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_df(self):
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch(ano=2024)

        assert len(df) == 1
        assert "ano" in df.columns
        assert "porto" in df.columns
        assert "peso_bruto_ton" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_with_filters(self):
        mock_fn = make_source(_make_df())
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            ano=2024,
            mercadoria="Soja",
            porto="Santos",
            uf="SP",
            sentido="embarque",
            tipo_navegacao="Longo Curso",
            natureza_carga="Granel Sólido",
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["mercadoria"] == "Soja"
        assert call_kwargs["porto"] == "Santos"
        assert call_kwargs["uf"] == "SP"
        assert call_kwargs["sentido"] == "embarque"
        assert call_kwargs["tipo_navegacao"] == "Longo Curso"
        assert call_kwargs["natureza_carga"] == "Granel Sólido"

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch(ano=2024, return_meta=True)

        assert meta.dataset == "movimentacao_portuaria"
        assert meta.contract_version == "1.0"
        assert "antaq" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = MovimentacaoPortuariaDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch(ano=2024)


class TestMovimentacaoPortuariaInfo:
    def test_source_antaq(self):
        assert len(MOVIMENTACAO_PORTUARIA_INFO.sources) == 1
        assert MOVIMENTACAO_PORTUARIA_INFO.sources[0].name == "antaq"

    def test_products_empty(self):
        assert MOVIMENTACAO_PORTUARIA_INFO.products == []

    def test_license(self):
        assert MOVIMENTACAO_PORTUARIA_INFO.license == "livre"

    def test_contract_version(self):
        assert MOVIMENTACAO_PORTUARIA_INFO.contract_version == "1.0"


class TestMovimentacaoPortuariaFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_antaq_forwards_params(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.antaq.movimentacao",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.movimentacao_portuaria import _fetch_antaq

            await _fetch_antaq(
                "",
                ano=2024,
                tipo_navegacao="Longo Curso",
                natureza_carga="Granel Sólido",
                mercadoria="Soja",
                porto="Santos",
                uf="SP",
                sentido="Embarcados",
            )
        mock_fn.assert_called_once_with(
            ano=2024,
            tipo_navegacao="Longo Curso",
            natureza_carga="Granel Sólido",
            mercadoria="Soja",
            porto="Santos",
            uf="SP",
            sentido="Embarcados",
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_antaq_defaults(self):
        from unittest.mock import AsyncMock, patch

        from .conftest import mock_source_meta

        df = _make_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.antaq.movimentacao",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.movimentacao_portuaria import _fetch_antaq

            await _fetch_antaq("", ano=2024)
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo_navegacao"] is None
        assert kwargs["natureza_carga"] is None
        assert kwargs["mercadoria"] is None
        assert kwargs["porto"] is None
        assert kwargs["uf"] is None
        assert kwargs["sentido"] is None
