from __future__ import annotations

import re

from agrobr.constants import URLS, Fonte

CKAN_API = URLS[Fonte.ZARC]["ckan_api"]
DATASET_SLUG = "tabua-de-risco-zoneamento-agricola-de-risco-climatico"

CULTURAS_ZARC: dict[str, str] = {
    "Soja": "soja",
    "Milho 1a Safra": "milho_1",
    "Milho 2a Safra": "milho_2",
    "Milho 1a Safra consorciado com Braquiaria": "milho_1_braquiaria",
    "Milho 2a Safra consorciado com Braquiaria": "milho_2_braquiaria",
    "Trigo": "trigo",
    "Trigo - Duplo Proposito": "trigo_duplo_proposito",
    "Arroz": "arroz",
    "Feijao": "feijao",
    "Feijao 2a Safra": "feijao_2",
    "Feijao Caupi": "feijao_caupi",
    "Algodao Herbaceo": "algodao",
    "Amendoim": "amendoim",
    "Aveia": "aveia",
    "Cevada Cervejeira": "cevada_cervejeira",
    "Cevada Graos": "cevada_graos",
    "Girassol": "girassol",
    "Mamona": "mamona",
    "Sorgo Granifero": "sorgo",
    "Sorgo Granifero 2a Safra": "sorgo_2",
    "Sorgo Forrageiro": "sorgo_forrageiro",
    "Sorgo Forrageiro 2a Safra": "sorgo_forrageiro_2",
    "Cafe Arabica": "cafe_arabica",
    "Cafe Canefora": "cafe_canefora",
    "Cana-de-Acucar": "cana",
    "Banana Cavendish - Implantacao": "banana_cavendish",
    "Laranja": "laranja",
    "Mandioca": "mandioca",
    "Batata Industria": "batata_industria",
    "Batata Mesa": "batata_mesa",
    "Cebola": "cebola",
    "Melancia": "melancia",
}

SOLOS: dict[int, str] = {
    1: "arenoso",
    2: "medio",
    3: "argiloso",
    11: "AD1_24mm",
    12: "AD2_32mm",
    13: "AD3_42mm",
    14: "AD4_55mm",
    15: "AD5_72mm",
    16: "AD6_95mm",
}

DEC_COLS: list[str] = [f"dec{i}" for i in range(1, 37)]

COLUNAS_SAIDA: list[str] = [
    "cultura",
    "safra",
    "geocodigo",
    "uf",
    "municipio",
    "solo_codigo",
    "ciclo_codigo",
    "clima",
    "manejo",
    "portaria",
    *DEC_COLS,
]

_SAFRA_RE = re.compile(r"(\d{4}/\d{4})")


def build_ckan_package_url(slug: str) -> str:
    return f"{CKAN_API}/package_show?id={slug}"


def _csv_resources(resources: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in resources if r.get("format", "").upper() in ("CSV", "")]


def match_safra_resource(resources: list[dict[str, str]], safra: str) -> str | None:
    """Retorna URL do CSV para a safra solicitada.

    Match no campo `name` do CKAN:
      safra="2025/2026" -> match "2025/2026" in resource["name"]
      safra="perene"    -> match "perene" in resource["name"] (case-insensitive)
    """
    safra_lower = safra.lower()
    for r in _csv_resources(resources):
        if safra_lower in r["name"].lower():
            return r["url"]
    return None


def extract_safras(resources: list[dict[str, str]]) -> list[str]:
    """Extrai lista de safras disponiveis dos recursos CKAN."""
    safras_ano: list[str] = []
    has_perene = False

    for r in _csv_resources(resources):
        m = _SAFRA_RE.search(r["name"])
        if m:
            safras_ano.append(m.group(1))
        elif "perene" in r["name"].lower():
            has_perene = True

    result = sorted(safras_ano)
    if has_perene:
        result.append("perene")
    return result
