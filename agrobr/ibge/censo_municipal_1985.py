from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result

logger = structlog.get_logger()

_DATA_DIR = Path(__file__).parent.parent / "data" / "censo_1985"

TABELAS_CENSO_MUNICIPAL_1985: dict[int, str] = {
    67: "propriedade_terras",
    68: "condicao_legal_terras",
    69: "classe_atividade_economica",
    70: "condicao_produtor",
    71: "residencia_produtor",
    72: "forma_administracao",
    73: "cooperativas",
    74: "servicos_empreitada",
    75: "uso_forca_trabalho",
    76: "assistencia_tecnica",
    77: "fertilizantes_defensivos",
    78: "conservacao_solo",
    79: "irrigacao",
    80: "inseminacao_ordenha",
    81: "terras_fora_area",
    82: "parcelas",
    83: "terras_proprias_terceiros",
    84: "grupos_area_total",
    85: "grupos_area_complemento",
    86: "utilizacao_terras",
    87: "pessoal_ocupado",
    88: "grupos_pessoal_ocupado",
    89: "silos_armazenamento",
    90: "maquinas_instrumentos",
    91: "meios_transporte",
    92: "energia_eletrica",
    93: "bens_despesas",
    94: "investimentos",
    95: "valor_bens_invest_financ",
    96: "despesas",
    97: "efetivo_bubalinos_machos",
    98: "efetivo_bubalinos_femeas",
    99: "efetivo_equinos",
    100: "efetivo_asininos",
    101: "efetivo_muares",
    102: "efetivo_bovinos",
    103: "efetivo_suinos",
    104: "efetivo_caprinos",
    105: "efetivo_coelhos",
    106: "efetivo_ovinos",
    107: "efetivo_aves",
    108: "producao_leite_ovos",
    109: "producao_la_mel",
    110: "producao_animal_cont",
    111: "colheita_lav_temporaria",
    112: "lavoura_permanente",
    113: "horticultura",
    114: "produtos_extrativos",
    115: "silvicultura",
    116: "silvicultura_cont",
    117: "transformacao_beneficiamento",
    118: "transformacao_cont",
    119: "producao_particular",
}

TEMAS_CENSO_MUNICIPAL_1985: dict[str, int] = {v: k for k, v in TABELAS_CENSO_MUNICIPAL_1985.items()}

TEMAS_DISPONIVEIS: list[str] = sorted(TEMAS_CENSO_MUNICIPAL_1985)

_UNIDADE_EXACT: dict[str, str] = {
    "nascidos": "cabeças",
    "vitimados": "cabeças",
    "comprados": "cabeças",
    "vendidos": "cabeças",
}

_UNIDADE_PREFIX: list[tuple[str, str]] = [
    ("area_ha_", "hectares"),
    ("estab_", "estabelecimentos"),
    ("inform_", "informantes"),
    ("num_pessoas_", "pessoas"),
    ("efetivo_", "cabeças"),
    ("qtde_", "toneladas"),
    ("valor_", "mil_cruzeiros"),
    ("val_", "unidades"),
]

_VALID_NIVEIS = {"total", "mesorregiao", "microrregiao", "municipio"}


@lru_cache(maxsize=1)
def _load_index() -> dict[int, dict[str, Any]]:
    path = _DATA_DIR / "_index.csv"
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    result: dict[int, dict[str, Any]] = {}
    for _, row in df.iterrows():
        result[int(row["table_num"])] = {
            "tema": row["tema"],
            "ufs": int(row["ufs"]),
            "rows": int(row["rows"]),
            "municipios": int(row["municipios"]),
            "data_cols": int(row["data_cols"]),
            "colunas": [c.strip() for c in str(row["colunas"]).split(", ")],
            "alta": int(row["alta"]),
            "media": int(row["media"]),
            "baixa": int(row["baixa"]),
        }
    return result


def _load_csv(table_num: int) -> pd.DataFrame:
    path = _DATA_DIR / f"tab_{table_num:03d}.csv"
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")


def _resolve_unidade(col_name: str) -> str:
    if col_name in _UNIDADE_EXACT:
        return _UNIDADE_EXACT[col_name]
    for prefix, unidade in _UNIDADE_PREFIX:
        if col_name.startswith(prefix):
            return unidade
    return "unidades"


def _batch_resolve_localidade_cod(df: pd.DataFrame) -> pd.Series:
    from agrobr.normalize import municipalities

    result = pd.Series(pd.NA, index=df.index, dtype="Int64")
    mask = df["nivel"] == "municipio"
    if not mask.any():
        return result

    unique = df.loc[mask, ["uf", "localidade"]].drop_duplicates()
    unique = unique.copy()
    unique["_code"] = [
        municipalities.municipio_para_ibge(loc, uf=uf)
        for uf, loc in zip(unique["uf"], unique["localidade"])
    ]

    merged = (
        df.loc[mask, ["uf", "localidade"]]
        .reset_index()
        .merge(unique, on=["uf", "localidade"], how="left")
    )
    merged = merged.set_index("index")
    result.loc[mask] = merged["_code"]
    return result


def _parse_to_long(df: pd.DataFrame, tema: str, data_cols: list[str]) -> pd.DataFrame:
    from agrobr.ibge.client import get_uf_codes

    melted = df.melt(
        id_vars=["_uf", "_label", "_level", "confianca"],
        value_vars=data_cols,
        var_name="variavel",
        value_name="valor",
    )

    uf_codes = get_uf_codes()

    result = pd.DataFrame(
        {
            "ano": 1985,
            "uf": melted["_uf"].values,
            "uf_cod": melted["_uf"].map(lambda x: int(uf_codes[x])).values,
            "localidade": melted["_label"].values,
            "localidade_cod": pd.array([pd.NA] * len(melted), dtype="Int64"),
            "nivel": melted["_level"].values,
            "tema": tema,
            "categoria": "geral",
            "variavel": melted["variavel"].values,
            "valor": pd.to_numeric(melted["valor"], errors="coerce").values,
            "unidade": melted["variavel"].map(_resolve_unidade).values,
            "confianca": melted["confianca"].values,
            "fonte": "ibge_censo_agro_municipal_1985",
        }
    )

    return result


@overload
async def censo_agro_municipal_1985(
    tema: str,
    *,
    uf: str | None = ...,
    nivel: str | None = ...,
    as_polars: bool = ...,
    return_meta: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
async def censo_agro_municipal_1985(
    tema: str,
    *,
    uf: str | None = ...,
    nivel: str | None = ...,
    as_polars: bool = ...,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def censo_agro_municipal_1985(
    tema: str,
    *,
    uf: str | None = None,
    nivel: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    from agrobr.ibge.client import get_uf_codes

    t0 = time.perf_counter()
    tema_lower = tema.lower().strip()
    if tema_lower not in TEMAS_CENSO_MUNICIPAL_1985:
        raise ValueError(f"Tema '{tema}' inválido. Temas disponíveis: {TEMAS_DISPONIVEIS}")

    table_num = TEMAS_CENSO_MUNICIPAL_1985[tema_lower]
    raw = _load_csv(table_num)

    if uf:
        uf_upper = uf.upper().strip()
        uf_codes = get_uf_codes()
        if uf_upper not in uf_codes:
            raise ValueError(f"UF '{uf}' inválida.")
        raw = raw[raw["_uf"] == uf_upper]
        if raw.empty:
            raise ValueError(f"UF '{uf}' não tem dados para tema '{tema}'.")

    index_entry = _load_index()[table_num]
    data_cols = index_entry["colunas"]

    df = _parse_to_long(raw, tema_lower, data_cols)
    df["localidade_cod"] = _batch_resolve_localidade_cod(df)

    if nivel:
        nivel_lower = nivel.lower().strip()
        if nivel_lower not in _VALID_NIVEIS:
            raise ValueError(f"Nível '{nivel}' inválido. Opções: {sorted(_VALID_NIVEIS)}")
        df = df[df["nivel"] == nivel_lower]

    df = df[
        [
            "ano",
            "uf",
            "uf_cod",
            "localidade",
            "localidade_cod",
            "nivel",
            "tema",
            "categoria",
            "variavel",
            "valor",
            "unidade",
            "confianca",
            "fonte",
        ]
    ].reset_index(drop=True)

    parse_ms = int((time.perf_counter() - t0) * 1000)

    logger.info(
        "censo_municipal_1985_loaded",
        tema=tema_lower,
        uf=uf,
        nivel=nivel,
        rows=len(df),
    )

    meta = build_source_meta(
        "ibge.censo_agro_municipal_1985",
        "https://biblioteca.ibge.gov.br/index.php/biblioteca-catalogo?view=detalhes&id=768",
        "local_csv",
        0,
        parse_ms,
        df,
        1,
    )
    meta.from_cache = True
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


async def temas_censo_agro_municipal_1985() -> list[str]:
    return list(TEMAS_DISPONIVEIS)
