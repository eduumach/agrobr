from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_comexstat(produto: str, **kwargs: Any) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import comexstat

    ano = kwargs.get("ano")
    uf = kwargs.get("uf")

    result = await comexstat.exportacao(produto, ano=ano, uf=uf, return_meta=True)

    return _unpack_result(result)


async def _fetch_abiove(produto: str, **kwargs: Any) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import abiove
    from agrobr.utils.time import utcnow

    ano: int = kwargs.get("ano", utcnow().year - 1)
    mes: int | None = kwargs.get("mes")

    result = await abiove.exportacao(ano=ano, mes=mes, produto=produto, return_meta=True)

    df, meta = _unpack_result(result)
    if "volume_ton" in df.columns and "kg_liquido" not in df.columns:
        df["kg_liquido"] = df["volume_ton"] * 1000
    if "receita_usd_mil" in df.columns and "valor_fob_usd" not in df.columns:
        df["valor_fob_usd"] = df["receita_usd_mil"] * 1000
    return df, meta


EXPORTACAO_INFO = DatasetInfo(
    name="exportacao",
    description="Exportações agrícolas brasileiras por produto, UF e mês",
    sources=[
        DatasetSource(
            name="comexstat",
            priority=1,
            fetch_fn=_fetch_comexstat,
            description="ComexStat/MDIC (dados oficiais de comércio exterior)",
        ),
        DatasetSource(
            name="abiove",
            priority=2,
            fetch_fn=_fetch_abiove,
            description="ABIOVE (complexo soja — farelo, óleo, grão)",
        ),
    ],
    products=["soja", "milho", "cafe", "algodao", "acucar", "farelo_soja", "oleo_soja"],
    contract_version="1.0",
    update_frequency="monthly",
    typical_latency="M+1",
    source_url="https://comexstat.mdic.gov.br",
    source_institution="MDIC/ComexStat",
    min_date="1997-01-01",
    unit="kg / USD",
    license="livre",
)


class ExportacaoDataset(BaseDataset):
    info = EXPORTACAO_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        ano: int | None = None,
        uf: str | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info("dataset_fetch", dataset="exportacao", produto=produto, ano=ano)

        snapshot = get_snapshot()
        if snapshot and ano is None:
            ano = int(snapshot[:4])

        df, source_name, source_meta, attempted = await self._try_sources(
            produto, ano=ano, uf=uf, **kwargs
        )

        df = self._normalize(df, produto)
        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)

        return df

    def _normalize(self, df: pd.DataFrame, produto: str) -> pd.DataFrame:
        if "produto" not in df.columns:
            df["produto"] = produto

        return df


_exportacao = ExportacaoDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_exportacao)


async def exportacao(
    produto: str,
    ano: int | None = None,
    uf: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _exportacao.fetch(produto, ano=ano, uf=uf, return_meta=return_meta, **kwargs)
