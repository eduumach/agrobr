from __future__ import annotations

SAFRAS_URLS: dict[str, str] = {
    "2024/2025": "https://www.fundacaorioverde.com.br/wp-content/uploads/2025/07/Competicao-de-Cultivares-de-Soja-Safra-2024-25.pdf",
    "2025/2026": "https://fundacaorioverde.com.br/wp-content/uploads/2026/03/Competicao-de-Cultivares-de-Soja-Safra-25-26.pdf",
}

COLUNAS_SAIDA: list[str] = [
    "safra",
    "empresa",
    "cultivar",
    "grupo_maturacao",
    "ciclo_dias",
    "produtividade_1_epoca_sc_ha",
    "produtividade_2_epoca_sc_ha",
    "produtividade_3_epoca_sc_ha",
    "produtividade_4_epoca_sc_ha",
    "produtividade_media_sc_ha",
]

MIN_PDF_SIZE = 50_000
