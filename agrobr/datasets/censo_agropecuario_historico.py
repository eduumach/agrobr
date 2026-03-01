from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource
from agrobr.datasets.deterministic import get_snapshot
from agrobr.ibge._helpers import SIDRA_BASE
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_ibge_censo_agro_historico(
    tema: str, **kwargs: Any
) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import ibge

    uf = kwargs.get("uf")
    nivel = kwargs.get("nivel", "uf")

    result = await ibge.censo_agro_historico(tema, uf=uf, nivel=nivel, return_meta=True)

    if isinstance(result, tuple):
        return result[0], result[1]
    return result, None


CENSO_AGROPECUARIO_HISTORICO_INFO = DatasetInfo(
    name="censo_agropecuario_historico",
    description="Série histórica do Censo Agropecuário (1920-2006) — dados por UF via SIDRA",
    sources=[
        DatasetSource(
            name="ibge_censo_agro_historico",
            priority=1,
            fetch_fn=_fetch_ibge_censo_agro_historico,
            description="IBGE Censo Agropecuário série histórica via SIDRA",
        ),
    ],
    products=[
        "estabelecimentos_area",
        "uso_terra",
        "pessoal_tratores",
        "condicao_produtor",
        "efetivo_animais",
        "producao_animal",
        "producao_vegetal",
        "lavoura_permanente",
        "lavoura_temporaria",
    ],
    contract_version="1.0",
    update_frequency="never",
    typical_latency="N/A",
    source_url=SIDRA_BASE,
    source_institution="IBGE",
    min_date="1920-01-01",
    unit="estabelecimentos / hectares / cabeças / toneladas",
    license="livre",
)


class CensoAgropecuarioHistoricoDataset(BaseDataset):
    info = CENSO_AGROPECUARIO_HISTORICO_INFO

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
            dataset="censo_agropecuario_historico",
            produto=produto,
            uf=uf,
        )

        snapshot = get_snapshot()

        df, source_name, source_meta, attempted = await self._try_sources(
            produto, uf=uf, nivel=nivel, **kwargs
        )

        self._validate_contract(df)

        if return_meta:
            now = datetime.now(UTC)
            meta = MetaInfo(
                source=f"datasets.censo_agropecuario_historico/{source_name}",
                source_url=source_meta.source_url if source_meta else "",
                source_method="dataset",
                fetched_at=source_meta.fetched_at if source_meta else now,
                records_count=len(df),
                columns=df.columns.tolist(),
                from_cache=False,
                parser_version=source_meta.parser_version if source_meta else 1,
                dataset="censo_agropecuario_historico",
                contract_version=self.info.contract_version,
                snapshot=snapshot,
                attempted_sources=attempted,
                selected_source=source_name,
                fetch_timestamp=now,
            )
            return df, meta

        return df


_censo_agropecuario_historico = CensoAgropecuarioHistoricoDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_censo_agropecuario_historico)


async def censo_agropecuario_historico(
    tema: str,
    uf: str | None = None,
    nivel: str = "uf",
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _censo_agropecuario_historico.fetch(
        tema, uf=uf, nivel=nivel, return_meta=return_meta, **kwargs
    )
