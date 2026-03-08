from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.models import MetaInfo

logger = structlog.get_logger()


async def _fetch_zarc(
    produto: str,  # noqa: ARG001
    **kwargs: Any,
) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import zarc

    result = await zarc.zoneamento(
        cultura=kwargs.get("cultura"),
        uf=kwargs.get("uf"),
        municipio=kwargs.get("municipio"),
        safra=kwargs.get("safra"),
        solo=kwargs.get("solo"),
        ciclo=kwargs.get("ciclo"),
        return_meta=True,
    )
    return _unpack_result(result)


ZONEAMENTO_AGRICOLA_INFO = DatasetInfo(
    name="zoneamento_agricola",
    description="Zoneamento Agrícola de Risco Climático — janelas de plantio por município/cultura/solo (ZARC/MAPA)",
    sources=[
        DatasetSource(
            name="zarc",
            priority=1,
            fetch_fn=_fetch_zarc,
            description="ZARC — Zoneamento Agrícola de Risco Climático (MAPA/Embrapa)",
        ),
    ],
    products=[],
    contract_version="1.0",
    update_frequency="yearly",
    typical_latency="safra+3m",
    source_url="https://indicadores.agricultura.gov.br/zarc/index.htm",
    source_institution="MAPA/Embrapa",
    unit="risco 0-5 por decêndio",
    license="livre",
)


class ZoneamentoAgricolaDataset(BaseDataset):
    info = ZONEAMENTO_AGRICOLA_INFO

    def _validate_produto(self, produto: str) -> None:
        pass

    async def fetch(  # type: ignore[override]
        self,
        *,
        cultura: str | None = None,
        uf: str | None = None,
        municipio: int | str | None = None,
        safra: str | None = None,
        solo: int | None = None,
        ciclo: int | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info(
            "dataset_fetch",
            dataset="zoneamento_agricola",
            cultura=cultura,
            uf=uf,
        )

        snapshot = get_snapshot()

        df, source_name, source_meta, attempted = await self._try_sources(
            "",
            cultura=cultura,
            uf=uf,
            municipio=municipio,
            safra=safra,
            solo=solo,
            ciclo=ciclo,
            **kwargs,
        )

        df = self._normalize(df)
        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)
        return df

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


_zoneamento_agricola = ZoneamentoAgricolaDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_zoneamento_agricola)


async def zoneamento_agricola(
    *,
    cultura: str | None = None,
    uf: str | None = None,
    municipio: int | str | None = None,
    safra: str | None = None,
    solo: int | None = None,
    ciclo: int | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _zoneamento_agricola.fetch(
        cultura=cultura,
        uf=uf,
        municipio=municipio,
        safra=safra,
        solo=solo,
        ciclo=ciclo,
        return_meta=return_meta,
        **kwargs,
    )
