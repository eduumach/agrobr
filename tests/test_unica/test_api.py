from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.unica import api as unica_api
from agrobr.unica.models import COLUNAS_HISTORICO, COLUNAS_RESUMO, COLUNAS_SERIES
from agrobr.utils.warnings import warn_once_reset

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "unica"
PDF_URL = "https://unicadata.com.br/arquivos/pdfs/2026/05/3d26022108c8712d1a4a68dc4fbbb940.pdf"
XLSX_URL = "https://unicadata.com.br/xlsHPM.php?produto=acucar"


@pytest.fixture(autouse=True)
def _reset_license_warning():
    warn_once_reset("unica_license")
    yield
    warn_once_reset("unica_license")


def _patch_pdf():
    pdf_bytes = (GOLDEN_DIR / "relatorio_quinzenal.pdf").read_bytes()
    return patch.object(
        unica_api.client,
        "fetch_quinzenal_pdf",
        new_callable=AsyncMock,
        return_value=(pdf_bytes, PDF_URL),
    )


def _patch_xlsx(nome: str = "hist_acucar.xlsx"):
    content = (GOLDEN_DIR / nome).read_bytes()
    return patch.object(
        unica_api.client,
        "fetch_historico_xlsx",
        new_callable=AsyncMock,
        return_value=(content, XLSX_URL),
    )


class TestLicenseWarning:
    @pytest.mark.asyncio
    async def test_primeira_chamada_emite_warning(self):
        with _patch_pdf(), pytest.warns(UserWarning, match="zona cinza"):
            await unica_api.moagem_quinzenal()


class TestMoagemQuinzenal:
    @pytest.mark.asyncio
    async def test_default_cana_todas_regioes(self):
        with _patch_pdf():
            df = await unica_api.moagem_quinzenal()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == COLUNAS_SERIES
        assert df["produto"].eq("cana").all()
        assert len(df) == 6
        assert set(df["regiao"]) == {"centro_sul", "sao_paulo", "demais_estados"}

    @pytest.mark.asyncio
    async def test_filtro_regiao(self):
        with _patch_pdf():
            df = await unica_api.moagem_quinzenal("acucar", regiao="centro_sul")

        assert df["regiao"].eq("centro_sul").all()
        assert df["produto"].eq("acucar").all()
        assert len(df) == 2

    @pytest.mark.asyncio
    async def test_produto_alias(self):
        with _patch_pdf():
            df = await unica_api.moagem_quinzenal("etanol total")

        assert df["produto"].eq("etanol_total").all()

    @pytest.mark.asyncio
    async def test_produto_invalido_raises_sem_fetch(self):
        with pytest.raises(ValueError, match="inválido para UNICA"):
            await unica_api.moagem_quinzenal("soja")

    @pytest.mark.asyncio
    async def test_regiao_invalida_raises_sem_fetch(self):
        with pytest.raises(ValueError, match="Região"):
            await unica_api.moagem_quinzenal("cana", regiao="nordeste")

    @pytest.mark.asyncio
    async def test_return_meta(self):
        with _patch_pdf():
            df, meta = await unica_api.moagem_quinzenal(return_meta=True)

        assert meta.source == "unica"
        assert meta.source_url == PDF_URL
        assert meta.records_count == len(df)
        assert meta.attempted_sources == ["unica"]

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        with _patch_pdf():
            result = await unica_api.moagem_quinzenal(as_polars=True)

        assert isinstance(result, pl.DataFrame)


class TestSafraResumo:
    @pytest.mark.asyncio
    async def test_default_acumulado(self):
        with _patch_pdf():
            df = await unica_api.safra_resumo()

        assert list(df.columns) == COLUNAS_RESUMO
        assert df["periodo"].eq("acumulado").all()
        assert len(df) == 33

    @pytest.mark.asyncio
    async def test_periodo_quinzena(self):
        with _patch_pdf():
            df = await unica_api.safra_resumo(periodo="quinzena")

        assert df["periodo"].eq("quinzena").all()
        assert len(df) == 33

    @pytest.mark.asyncio
    async def test_periodo_invalido_raises(self):
        with pytest.raises(ValueError, match="Período"):
            await unica_api.safra_resumo(periodo="mensal")


class TestProducaoHistorica:
    @pytest.mark.asyncio
    async def test_basico(self):
        with _patch_xlsx() as mock_fetch:
            df = await unica_api.producao_historica("açúcar", safra_inicio="2018/2019")

        assert list(df.columns) == COLUNAS_HISTORICO
        assert df["produto"].eq("acucar").all()
        assert len(df) == 81
        mock_fetch.assert_called_once_with("acucar", "2018/2019", None)

    @pytest.mark.asyncio
    async def test_produto_invalido_raises_sem_fetch(self):
        with pytest.raises(ValueError, match="inválido para UNICA"):
            await unica_api.producao_historica("laranja")

    @pytest.mark.asyncio
    async def test_return_meta(self):
        with _patch_xlsx():
            df, meta = await unica_api.producao_historica("acucar", return_meta=True)

        assert meta.source == "unica"
        assert meta.records_count == len(df)
        assert meta.selected_source == "unica"
