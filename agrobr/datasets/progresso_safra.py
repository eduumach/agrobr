from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.datasets.base import BaseDataset, DatasetInfo, DatasetSource, _unpack_result
from agrobr.datasets.deterministic import get_snapshot
from agrobr.models import MetaInfo

logger = structlog.get_logger()

PRODUCTS = ["algodao", "arroz", "feijao_1", "milho_1", "milho_2", "soja", "trigo"]


async def _fetch_conab(produto: str, **kwargs: Any) -> tuple[pd.DataFrame, MetaInfo | None]:
    from agrobr.conab.progresso import api as progresso_api
    from agrobr.conab.progresso.models import normalizar_cultura

    cultura = normalizar_cultura(produto)
    estado = kwargs.get("estado")
    operacao = kwargs.get("operacao")

    fwd_kwargs: dict[str, Any] = {}
    if "semana_url" in kwargs:
        fwd_kwargs["semana_url"] = kwargs["semana_url"]

    result = await progresso_api.progresso_safra(
        cultura=cultura,
        estado=estado,
        operacao=operacao,
        return_meta=True,
        **fwd_kwargs,
    )

    return _unpack_result(result)


PROGRESSO_SAFRA_INFO = DatasetInfo(
    name="progresso_safra",
    description="Progresso semanal de semeadura e colheita (CONAB)",
    sources=[
        DatasetSource(
            name="conab",
            priority=1,
            fetch_fn=_fetch_conab,
            description="CONAB (Companhia Nacional de Abastecimento)",
        ),
    ],
    products=PRODUCTS,
    contract_version="1.0",
    update_frequency="weekly",
    typical_latency="W+0",
    source_url="https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras/progresso-de-safra",
    source_institution="CONAB",
    unit="fração (0-1)",
    license="livre",
)


class ProgressoSafraDataset(BaseDataset):
    info = PROGRESSO_SAFRA_INFO

    async def fetch(  # type: ignore[override]
        self,
        produto: str,
        estado: str | None = None,
        operacao: str | None = None,
        return_meta: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
        logger.info("dataset_fetch", dataset="progresso_safra", produto=produto)

        snapshot = get_snapshot()

        df, source_name, source_meta, attempted = await self._try_sources(
            produto, estado=estado, operacao=operacao, **kwargs
        )

        df = self._normalize(df)
        self._validate_contract(df)

        if return_meta:
            return df, self._build_meta(df, source_name, source_meta, attempted, snapshot)

        return df

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


_progresso_safra = ProgressoSafraDataset()

from agrobr.datasets.registry import register  # noqa: E402

register(_progresso_safra)


async def progresso_safra(
    produto: str,
    estado: str | None = None,
    operacao: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    return await _progresso_safra.fetch(
        produto, estado=estado, operacao=operacao, return_meta=return_meta, **kwargs
    )
