from __future__ import annotations

from typing import Any, Literal

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.ibge._helpers import SIDRA_BASE
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_ibge_extracao_vegetal(
    produto: str, **kwargs: Any
) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import ibge

    ano = kwargs.get("ano")
    nivel = kwargs.get("nivel", "uf")
    uf = kwargs.get("uf")
    variavel = kwargs.get("variavel", "quantidade_produzida")

    result = await ibge.extracao_vegetal(
        produto, ano=ano, nivel=nivel, uf=uf, variavel=variavel, return_meta=True
    )

    return _unpack_result(result)


EXTRATIVISMO_VEGETAL_INFO = DatasetInfo(
    name="extrativismo_vegetal",
    description="Produção extrativista vegetal (açaí, castanha, erva-mate, etc.) por UF ou município",
    sources=[
        DatasetSource(
            name="ibge_extracao_vegetal",
            priority=1,
            fetch_fn=_fetch_ibge_extracao_vegetal,
            description="IBGE PEVS Extração Vegetal",
        ),
    ],
    products=[
        "acai",
        "castanha_para",
        "erva_mate",
        "palmito",
        "pequi_fruto",
        "babacu",
        "piacava",
        "carnauba_cera",
        "carvao",
        "lenha",
        "madeira_tora",
        "hevea_coagulado",
    ],
    contract_version="1.0",
    update_frequency="yearly",
    typical_latency="Y+1",
    source_url=SIDRA_BASE,
    source_institution="IBGE",
    min_date="1986-01-01",
    unit="Toneladas / Metros cúbicos",
    license="livre",
)


class ExtrativsmoVegetalDataset(BaseDataset):
    info = EXTRATIVISMO_VEGETAL_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        ano: int | None = None,
        nivel: Literal["brasil", "uf", "municipio"] = "uf",
        uf: str | None = None,
        variavel: str = "quantidade_produzida",
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info("dataset_fetch", dataset="extrativismo_vegetal", produto=produto, ano=ano)

        snapshot = get_snapshot()
        if snapshot and ano is None:
            ano = int(snapshot[:4]) - 1

        df, source_name, source_meta, attempted = await self._try_sources(
            produto, ano=ano, nivel=nivel, uf=uf, variavel=variavel, **kwargs
        )

        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)

        return df


_extrativismo_vegetal = ExtrativsmoVegetalDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_extrativismo_vegetal)


async def extrativismo_vegetal(
    produto: str,
    ano: int | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    uf: str | None = None,
    variavel: str = "quantidade_produzida",
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _extrativismo_vegetal.fetch(
        produto, ano=ano, nivel=nivel, uf=uf, variavel=variavel, return_meta=return_meta, **kwargs
    )
