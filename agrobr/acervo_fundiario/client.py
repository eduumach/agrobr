from __future__ import annotations

import structlog

from agrobr.exceptions import SourceUnavailableError
from agrobr.http.settings import get_timeout
from agrobr.utils.geo import fetch_wfs

from .models import (
    ASSENTAMENTOS_LAYER,
    ASSENTAMENTOS_PROPERTY_NAMES,
    MAX_FEATURES_ASSENTAMENTOS,
    MAX_FEATURES_SIGEF,
    MAX_FEATURES_SNCI,
    SIGEF_LAYERS,
    SIGEF_PROPERTY_NAMES,
    SNCI_LAYERS,
    SNCI_PROPERTY_NAMES,
    WFS_BASE,
    WFS_VERSION,
)

logger = structlog.get_logger()

TIMEOUT = get_timeout(read=180.0)


def _build_url(
    layer_prefix: str,
    uf: str,
    *,
    max_features: int,
    property_names: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> str:
    layer = f"{layer_prefix}_{uf.lower()}"
    url = (
        f"{WFS_BASE}?tema={layer}"
        f"&service=WFS&version={WFS_VERSION}&request=GetFeature"
        f"&typeName={layer}"
        f"&maxFeatures={max_features}"
    )
    if property_names:
        url += f"&propertyName={','.join(property_names)}"
    if bbox:
        url += f"&BBOX={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    return url


def _check_exception_report(content: bytes, uf: str, url: str) -> None:
    probe = content[:500]
    if b"ServiceException" in probe or b"ExceptionReport" in probe or b"msWFSGetFeature" in probe:
        raise SourceUnavailableError(
            source="acervo_fundiario",
            url=url,
            last_error=f"WFS retornou ExceptionReport para UF={uf} (possivel layer sem SRS configurado)",
        )


async def fetch_sigef(
    uf: str,
    tipo: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    geo: bool = False,
) -> tuple[bytes, str]:
    layer_prefix = SIGEF_LAYERS[tipo]
    url = _build_url(
        layer_prefix,
        uf,
        max_features=MAX_FEATURES_SIGEF,
        property_names=None if geo else SIGEF_PROPERTY_NAMES,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="acervo_fundiario", timeout=TIMEOUT)
    _check_exception_report(content, uf, url)
    logger.info("acervo_fundiario_sigef_fetch", uf=uf, tipo=tipo, geo=geo, size=len(content))
    return content, url


async def fetch_snci(
    uf: str,
    tipo: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    geo: bool = False,
) -> tuple[bytes, str]:
    layer_prefix = SNCI_LAYERS[tipo]
    url = _build_url(
        layer_prefix,
        uf,
        max_features=MAX_FEATURES_SNCI,
        property_names=None if geo else SNCI_PROPERTY_NAMES,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="acervo_fundiario", timeout=TIMEOUT)
    _check_exception_report(content, uf, url)
    logger.info("acervo_fundiario_snci_fetch", uf=uf, tipo=tipo, geo=geo, size=len(content))
    return content, url


async def fetch_assentamentos(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    geo: bool = False,
) -> tuple[bytes, str]:
    url = _build_url(
        ASSENTAMENTOS_LAYER,
        uf,
        max_features=MAX_FEATURES_ASSENTAMENTOS,
        property_names=None if geo else ASSENTAMENTOS_PROPERTY_NAMES,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="acervo_fundiario", timeout=TIMEOUT)
    _check_exception_report(content, uf, url)
    logger.info("acervo_fundiario_assentamentos_fetch", uf=uf, geo=geo, size=len(content))
    return content, url
