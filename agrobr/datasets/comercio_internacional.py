from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.comtrade.models import HS_PRODUTOS_AGRO
from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.models import MetaInfo

logger = structlog.get_logger()

_PRODUCTS = sorted(HS_PRODUTOS_AGRO.keys())


async def _fetch_comtrade(produto: str, **kwargs: Any) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr import comtrade

    reporter: str = kwargs.get("reporter", "BR") or "BR"
    partner: str | None = kwargs.get("partner")
    fluxo: str = kwargs.get("fluxo", "X")
    periodo: str | int | None = kwargs.get("periodo")
    freq: str = kwargs.get("freq", "A")
    api_key: str | None = kwargs.get("api_key")

    result = await comtrade.comercio(
        produto,
        reporter=reporter,
        partner=partner,
        fluxo=fluxo,
        periodo=periodo,
        freq=freq,
        api_key=api_key,
        return_meta=True,
    )
    return _unpack_result(result)


COMERCIO_INTERNACIONAL_INFO = DatasetInfo(
    name="comercio_internacional",
    description="Comércio internacional bilateral de commodities agrícolas — UN Comtrade (HS codes, qualquer reporter/partner)",
    sources=[
        DatasetSource(
            name="comtrade",
            priority=1,
            fetch_fn=_fetch_comtrade,
            description="UN Comtrade — comércio bilateral global por HS code",
        ),
    ],
    products=_PRODUCTS,
    contract_version="1.0",
    update_frequency="monthly",
    typical_latency="M+2",
    source_url="https://comtradeplus.un.org",
    source_institution="United Nations / Comtrade",
    unit="kg / USD",
    license="livre",
)


class ComercioInternacionalDataset(BaseDataset):
    info = COMERCIO_INTERNACIONAL_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        *,
        reporter: str = "BR",
        partner: str | None = None,
        fluxo: str = "X",
        periodo: str | None = None,
        freq: str = "A",
        api_key: str | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info("dataset_fetch", dataset="comercio_internacional", produto=produto)

        snapshot = get_snapshot()
        if snapshot and periodo is None:
            periodo = snapshot[:4]

        df, source_name, source_meta, attempted = await self._try_sources(
            produto,
            reporter=reporter,
            partner=partner,
            fluxo=fluxo,
            periodo=periodo,
            freq=freq,
            api_key=api_key,
            **kwargs,
        )

        df = self._normalize(df)
        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)
        return df

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


_comercio_internacional = ComercioInternacionalDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_comercio_internacional)


async def comercio_internacional(
    produto: str,
    *,
    reporter: str = "BR",
    partner: str | None = None,
    fluxo: str = "X",
    periodo: str | None = None,
    freq: str = "A",
    api_key: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _comercio_internacional.fetch(
        produto,
        reporter=reporter,
        partner=partner,
        fluxo=fluxo,
        periodo=periodo,
        freq=freq,
        api_key=api_key,
        return_meta=return_meta,
        **kwargs,
    )
