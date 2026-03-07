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

    result = await comexstat.importacao(produto, ano=ano, uf=uf, return_meta=True)

    return _unpack_result(result)


IMPORTACAO_INFO = DatasetInfo(
    name="importacao",
    description="Importações agrícolas brasileiras por produto, UF e mês",
    sources=[
        DatasetSource(
            name="comexstat",
            priority=1,
            fetch_fn=_fetch_comexstat,
            description="ComexStat/MDIC (dados oficiais de comércio exterior)",
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


class ImportacaoDataset(BaseDataset):
    info = IMPORTACAO_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        ano: int | None = None,
        uf: str | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info("dataset_fetch", dataset="importacao", produto=produto, ano=ano)

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


_importacao = ImportacaoDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_importacao)


async def importacao(
    produto: str,
    ano: int | None = None,
    uf: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _importacao.fetch(produto, ano=ano, uf=uf, return_meta=return_meta, **kwargs)
