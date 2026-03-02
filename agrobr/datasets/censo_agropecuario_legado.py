from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_ibge_censo_agro_legado(
    tema: str, **kwargs: Any
) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr.ibge import legacy_api

    uf = kwargs.get("uf")
    nivel = kwargs.get("nivel", "uf")

    result = await legacy_api.censo_agro_legado(tema, uf=uf, nivel=nivel, return_meta=True)

    return _unpack_result(result)


CENSO_AGROPECUARIO_LEGADO_INFO = DatasetInfo(
    name="censo_agropecuario_legado",
    description="Censo Agropecuário 1995/96 — temas legados via FTP (XLS)",
    sources=[
        DatasetSource(
            name="ibge_censo_agro_legado",
            priority=1,
            fetch_fn=_fetch_ibge_censo_agro_legado,
            description="IBGE Censo Agropecuário 1995/96 via FTP (XLS legado)",
        ),
    ],
    products=[
        "tecnologia",
        "pessoal_ocupado",
        "maquinas",
        "producao_animal",
        "valor_producao",
        "financeiro",
    ],
    contract_version="1.0",
    update_frequency="never",
    typical_latency="N/A",
    source_url="https://ftp.ibge.gov.br/Censo_Agropecuario/Censo_Agropecuario_1995_96",
    source_institution="IBGE",
    min_date="1995-01-01",
    unit="estabelecimentos / pessoas / unidades / R$",
    license="livre",
)


class CensoAgropecuarioLegadoDataset(BaseDataset):
    info = CENSO_AGROPECUARIO_LEGADO_INFO

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
            dataset="censo_agropecuario_legado",
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


_censo_agropecuario_legado = CensoAgropecuarioLegadoDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_censo_agropecuario_legado)


async def censo_agropecuario_legado(
    tema: str,
    uf: str | None = None,
    nivel: str = "uf",
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _censo_agropecuario_legado.fetch(
        tema, uf=uf, nivel=nivel, return_meta=return_meta, **kwargs
    )
