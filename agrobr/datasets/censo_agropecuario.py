from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.ibge._helpers import SIDRA_BASE
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_ibge_censo_agro(tema: str, **kwargs: Any) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import ibge

    uf = kwargs.get("uf")
    nivel = kwargs.get("nivel", "uf")

    result = await ibge.censo_agro(tema, uf=uf, nivel=nivel, return_meta=True)

    return _unpack_result(result)


CENSO_AGROPECUARIO_INFO = DatasetInfo(
    name="censo_agropecuario",
    description="Dados do Censo Agropecuário por tema, categoria e UF",
    sources=[
        DatasetSource(
            name="ibge_censo_agro",
            priority=1,
            fetch_fn=_fetch_ibge_censo_agro,
            description="IBGE Censo Agropecuário via SIDRA",
        ),
    ],
    products=[
        "efetivo_rebanho",
        "uso_terra",
        "lavoura_temporaria",
        "lavoura_permanente",
        "preparo_solo",
        "adubacao",
        "calagem",
        "agrotoxicos",
        "praticas_agricolas",
        "irrigacao",
    ],
    contract_version="1.0",
    update_frequency="decennial",
    typical_latency="Y+2 anos",
    source_url=SIDRA_BASE,
    source_institution="IBGE",
    min_date="1995-01-01",
    unit="cabeças / hectares / toneladas",
    license="livre",
)


class CensoAgropecuarioDataset(BaseDataset):
    info = CENSO_AGROPECUARIO_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        uf: str | None = None,
        nivel: str = "uf",
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info(
            "dataset_fetch",
            dataset="censo_agropecuario",
            produto=produto,
            uf=uf,
        )

        snapshot = get_snapshot()

        df, source_name, source_meta, attempted = await self._try_sources(
            produto, uf=uf, nivel=nivel, **kwargs
        )

        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)

        return df


_censo_agropecuario = CensoAgropecuarioDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_censo_agropecuario)


async def censo_agropecuario(
    tema: str,
    uf: str | None = None,
    nivel: str = "uf",
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _censo_agropecuario.fetch(
        tema, uf=uf, nivel=nivel, return_meta=return_meta, **kwargs
    )
