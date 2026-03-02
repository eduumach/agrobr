from __future__ import annotations

from pydantic import BaseModel, field_validator

from agrobr.normalize.dates import MESES_PT as MESES_PT

ABIOVE_PRODUTOS: dict[str, str] = {
    "grao": "grao",
    "grão": "grao",
    "soja em grão": "grao",
    "soja em grao": "grao",
    "soja grão": "grao",
    "soja grao": "grao",
    "grain": "grao",
    "soybeans": "grao",
    "soybean": "grao",
    "farelo": "farelo",
    "farelo de soja": "farelo",
    "soybean meal": "farelo",
    "soymeal": "farelo",
    "meal": "farelo",
    "oleo": "oleo",
    "óleo": "oleo",
    "oleo de soja": "oleo",
    "óleo de soja": "oleo",
    "soybean oil": "oleo",
    "soyoil": "oleo",
    "oil": "oleo",
    "milho": "milho",
    "corn": "milho",
    "maize": "milho",
    "total": "total",
}


def normalize_produto(nome: str) -> str:
    key = nome.strip().lower()
    return ABIOVE_PRODUTOS.get(key, key)


class ExportacaoSoja(BaseModel):
    ano: int
    mes: int
    produto: str
    volume_ton: float
    receita_usd_mil: float | None = None

    @field_validator("mes")
    @classmethod
    def validate_mes(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError(f"mes deve ser 1-12, recebido {v}")
        return v

    @field_validator("produto", mode="before")
    @classmethod
    def normalize_produto_validator(cls, v: str) -> str:
        return normalize_produto(v)

    @field_validator("volume_ton")
    @classmethod
    def validate_volume(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"volume_ton não pode ser negativo: {v}")
        return v
