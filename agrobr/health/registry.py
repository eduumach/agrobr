"""Health check registry — maps every Fonte to its connectivity config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agrobr.constants import URLS, Fonte


@dataclass(frozen=True)
class SourceHealthConfig:
    source: Fonte
    url: str
    method: Literal["GET", "HEAD"] = "GET"
    timeout: float = 15.0
    expected_status: int = 200
    follow_redirects: bool = True
    has_deep_check: bool = False
    tier: Literal["critical", "standard", "best_effort"] = "standard"
    requires_api_key: bool = False
    api_key_env_var: str | None = None


def _build_registry() -> dict[Fonte, SourceHealthConfig]:
    """Build the registry by iterating constants.URLS with per-source overrides."""
    overrides: dict[Fonte, dict[str, Any]] = {
        Fonte.IBGE: {
            "url": URLS[Fonte.IBGE]["api"],
        },
        Fonte.BCB: {
            "url": URLS[Fonte.BCB]["base"],
        },
        Fonte.CEPEA: {
            "has_deep_check": True,
            "tier": "critical",
        },
        Fonte.IMEA: {
            "url": URLS[Fonte.IMEA]["cotacoes"],
        },
        Fonte.USDA: {
            "requires_api_key": True,
            "api_key_env_var": "AGROBR_USDA_API_KEY",
        },
        Fonte.INMET: {
            "requires_api_key": True,
            "api_key_env_var": "AGROBR_INMET_TOKEN",
        },
        Fonte.COMTRADE: {
            "requires_api_key": True,
            "api_key_env_var": "AGROBR_COMTRADE_API_KEY",
        },
    }

    registry: dict[Fonte, SourceHealthConfig] = {}

    for fonte in Fonte:
        urls = URLS.get(fonte)
        if not urls:
            continue

        fonte_overrides = overrides.get(fonte, {})
        url = fonte_overrides.pop("url", urls.get("base", ""))

        registry[fonte] = SourceHealthConfig(source=fonte, url=url, **fonte_overrides)

    return registry


HEALTH_REGISTRY: dict[Fonte, SourceHealthConfig] = _build_registry()

SOURCE_DATASET_MAP: dict[str, list[str]] = {
    "abiove": ["exportacao"],
    "anda": ["fertilizante"],
    "antaq": ["movimentacao_portuaria"],
    "b3": ["futuros_agricolas"],
    "bcb": ["credito_rural"],
    "cepea": ["preco_diario"],
    "comexstat": ["exportacao", "importacao"],
    "comtrade": ["comercio_internacional"],
    "conab": [
        "balanco",
        "custo_producao",
        "estimativa_safra",
        "preco_atacado",
        "producao_anual",
        "progresso_safra",
        "serie_historica_safra",
    ],
    "deral": ["condicao_lavouras"],
    "desmatamento": ["desmatamento"],
    "ibge": [
        "abate_trimestral",
        "censo_agropecuario",
        "censo_agropecuario_historico",
        "censo_agropecuario_legado",
        "censo_agropecuario_municipal_1985",
        "estimativa_safra",
        "extrativismo_vegetal",
        "leite_industrial",
        "pecuaria_municipal",
        "pib_agro",
        "producao_anual",
        "silvicultura",
    ],
    "inmet": ["clima"],
    "mapa_psr": ["seguro_rural"],
    "mapbiomas": ["uso_do_solo"],
    "nasa_power": ["clima"],
    "queimadas": ["queimadas"],
    "sicar": ["cadastro_rural"],
    "usda": ["oferta_demanda_global"],
    "zarc": ["zoneamento_agricola"],
}


def get_affected_datasets(source: Fonte) -> list[str]:
    """Return datasets affected when *source* is down."""
    return SOURCE_DATASET_MAP.get(source.value, [])
