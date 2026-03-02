from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
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

    return _unpack_result(result)


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
            return df, self._build_meta(
                df, source_name, source_meta, attempted, snapshot, from_cache=True
            )

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
