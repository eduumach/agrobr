from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource
from agrobr.datasets.deterministic import get_snapshot
from agrobr.ibge.censo_municipal_1985 import TEMAS_DISPONIVEIS
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_ibge_censo_municipal_1985(
    tema: str, **kwargs: Any
) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr.ibge import censo_municipal_1985

    uf = kwargs.get("uf")
    nivel = kwargs.get("nivel")

    result = await censo_municipal_1985.censo_agro_municipal_1985(
        tema, uf=uf, nivel=nivel, return_meta=True
    )

    if isinstance(result, tuple):
        return result[0], result[1]
    return result, None


CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO = DatasetInfo(
    name="censo_agropecuario_municipal_1985",
    description="Censo Agropecuário 1985 — dados municipais extraídos via OCR de PDFs do IBGE (22 UFs, 53 temas)",
    sources=[
        DatasetSource(
            name="ibge_censo_agro_municipal_1985",
            priority=1,
            fetch_fn=_fetch_ibge_censo_municipal_1985,
            description="Censo 1985 municipal via CSVs locais (OCR de PDFs IBGE)",
        ),
    ],
    products=TEMAS_DISPONIVEIS,
    contract_version="1.0",
    update_frequency="never",
    typical_latency="N/A",
    source_url="https://biblioteca.ibge.gov.br/index.php/biblioteca-catalogo?view=detalhes&id=768",
    source_institution="IBGE",
    min_date="1985-01-01",
    unit="estabelecimentos / hectares / cabeças / toneladas / unidades",
    license="livre",
)


class CensoAgropecuarioMunicipal1985Dataset(BaseDataset):
    info = CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        uf: str | None = None,
        nivel: str | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info(
            "dataset_fetch",
            dataset="censo_agropecuario_municipal_1985",
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
                source=f"datasets.censo_agropecuario_municipal_1985/{source_name}",
                source_url=source_meta.source_url if source_meta else "",
                source_method="dataset",
                fetched_at=source_meta.fetched_at if source_meta else now,
                records_count=len(df),
                columns=df.columns.tolist(),
                from_cache=True,
                parser_version=source_meta.parser_version if source_meta else 1,
                dataset="censo_agropecuario_municipal_1985",
                contract_version=self.info.contract_version,
                snapshot=snapshot,
                attempted_sources=attempted,
                selected_source=source_name,
                fetch_timestamp=now,
            )
            return df, meta

        return df


_censo_agropecuario_municipal_1985 = CensoAgropecuarioMunicipal1985Dataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_censo_agropecuario_municipal_1985)


async def censo_agropecuario_municipal_1985(
    tema: str,
    uf: str | None = None,
    nivel: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _censo_agropecuario_municipal_1985.fetch(
        tema, uf=uf, nivel=nivel, return_meta=return_meta, **kwargs
    )
