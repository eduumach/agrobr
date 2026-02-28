from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Literal, overload

import pandas as pd
import structlog

from agrobr import constants
from agrobr.cache.keys import build_cache_key
from agrobr.cache.policies import calculate_expiry
from agrobr.ibge import client
from agrobr.models import MetaInfo

logger = structlog.get_logger()

_LSPA_ALIASES: dict[str, list[str]] = {
    "milho": ["milho_1", "milho_2"],
    "feijao": ["feijao_1", "feijao_2", "feijao_3"],
    "amendoim": ["amendoim_1", "amendoim_2"],
    "batata": ["batata_1", "batata_2"],
}


def _expand_lspa_produto(produto: str) -> list[tuple[str, str]]:
    if produto in client.PRODUTOS_LSPA:
        return [(produto, client.PRODUTOS_LSPA[produto])]

    if produto in _LSPA_ALIASES:
        return [(sub, client.PRODUTOS_LSPA[sub]) for sub in _LSPA_ALIASES[produto]]

    all_valid = sorted(set(list(client.PRODUTOS_LSPA.keys()) + list(_LSPA_ALIASES.keys())))
    raise ValueError(f"Produto não suportado: {produto}. Disponíveis: {all_valid}")


@overload
async def pam(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variaveis: list[str] | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def pam(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variaveis: list[str] | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def pam(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variaveis: list[str] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_pam",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_pam_request",
        produto=produto,
        ano=ano,
        uf=uf,
        nivel=nivel,
    )

    produto_lower = produto.lower()
    if produto_lower not in client.PRODUTOS_PAM:
        raise ValueError(
            f"Produto não suportado: {produto}. Disponíveis: {list(client.PRODUTOS_PAM.keys())}"
        )

    produto_cod = client.PRODUTOS_PAM[produto_lower]

    if variaveis is None:
        variaveis = ["area_plantada", "area_colhida", "producao", "rendimento"]

    var_codes = []
    for var in variaveis:
        if var in client.VARIAVEIS:
            var_codes.append(client.VARIAVEIS[var])
        else:
            logger.warning(f"Variável desconhecida: {var}")

    nivel_map = {
        "brasil": "1",
        "uf": "3",
        "municipio": "6",
    }
    territorial_level = nivel_map.get(nivel, "3")

    ibge_code = "all"
    if uf:
        uf_ibge = client.uf_to_ibge_code(uf)
        if nivel == "municipio":
            ibge_code = f"in N3 {uf_ibge}"
        elif nivel == "uf":
            ibge_code = uf_ibge

    if ano is None:
        period = "last"
    elif isinstance(ano, list):
        period = ",".join(str(a) for a in ano)
    else:
        period = str(ano)

    df = await client.fetch_sidra(
        table_code=client.TABELAS["pam_nova"],
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=",".join(var_codes) if var_codes else None,
        period=period,
        classifications={"782": produto_cod},
    )

    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "ano_cod",
            "D2N": "ano",
            "D3C": "variavel_cod",
            "D3N": "variavel",
            "D4C": "produto_cod",
            "D4N": "produto_raw",
        },
    )

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    if "variavel" in df.columns and "valor" in df.columns:
        df_pivot = df.pivot_table(
            index=["localidade", "ano"] if "localidade" in df.columns else ["ano"],
            columns="variavel",
            values="valor",
            aggfunc="first",
        ).reset_index()

        rename_map = {
            "Área plantada": "area_plantada",
            "Área plantada ou destinada à colheita": "area_plantada",
            "Área colhida": "area_colhida",
            "Quantidade produzida": "producao",
            "Rendimento médio da produção": "rendimento",
            "Valor da produção": "valor_producao",
        }
        df_pivot = df_pivot.rename(columns=rename_map)
        df = df_pivot

    df["produto"] = produto_lower
    df["fonte"] = "ibge_pam"

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:pam",
        {"produto": produto, "ano": ano},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "pam")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_pam_success",
        produto=produto,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


@overload
async def lspa(
    produto: str,
    ano: int | str | None = None,
    mes: int | str | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def lspa(
    produto: str,
    ano: int | str | None = None,
    mes: int | str | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def lspa(
    produto: str,
    ano: int | str | None = None,
    mes: int | str | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_lspa",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_lspa_request",
        produto=produto,
        ano=ano,
        mes=mes,
        uf=uf,
    )

    produto_lower = produto.lower()
    sub_produtos = _expand_lspa_produto(produto_lower)

    if ano is None:
        from datetime import date

        ano = date.today().year

    period = f"{ano}{int(mes):02d}" if mes else ",".join(f"{ano}{m:02d}" for m in range(1, 13))

    territorial_level = "3" if uf else "1"
    ibge_code = client.uf_to_ibge_code(uf) if uf else "all"

    frames: list[pd.DataFrame] = []
    for sub_nome, sub_cod in sub_produtos:
        sub_df = await client.fetch_sidra(
            table_code=client.TABELAS["lspa"],
            territorial_level=territorial_level,
            ibge_territorial_code=ibge_code,
            period=period,
            classifications={"48": sub_cod},
        )

        sub_df = client.parse_sidra_response(sub_df)

        sub_df["ano"] = ano
        if mes:
            sub_df["mes"] = mes

        sub_df["produto"] = sub_nome
        sub_df["fonte"] = "ibge_lspa"
        frames.append(sub_df)

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:lspa",
        {"produto": produto, "ano": ano, "mes": mes},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "lspa")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_lspa_success",
        produto=produto,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


async def produtos_pam() -> list[str]:
    return list(client.PRODUTOS_PAM.keys())


async def produtos_lspa() -> list[str]:
    return list(client.PRODUTOS_LSPA.keys())


@overload
async def ppm(
    especie: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def ppm(
    especie: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def ppm(
    especie: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_ppm",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_ppm_request",
        especie=especie,
        ano=ano,
        uf=uf,
        nivel=nivel,
    )

    especie_lower = especie.lower()
    all_valid = sorted(
        list(client.REBANHOS_PPM.keys()) + list(client.PRODUTOS_ORIGEM_ANIMAL.keys())
    )

    is_rebanho = especie_lower in client.REBANHOS_PPM
    is_producao = especie_lower in client.PRODUTOS_ORIGEM_ANIMAL

    if not is_rebanho and not is_producao:
        raise ValueError(f"Espécie/produto não suportado: {especie}. Disponíveis: {all_valid}")

    nivel_map = {
        "brasil": "1",
        "uf": "3",
        "municipio": "6",
    }
    territorial_level = nivel_map.get(nivel, "3")

    ibge_code = "all"
    if uf:
        uf_ibge = client.uf_to_ibge_code(uf)
        if nivel == "municipio":
            ibge_code = f"in N3 {uf_ibge}"
        elif nivel == "uf":
            ibge_code = uf_ibge

    if ano is None:
        period = "last"
    elif isinstance(ano, list):
        period = ",".join(str(a) for a in ano)
    else:
        period = str(ano)

    classifications: dict[str, str | list[str]] = {}
    if is_rebanho:
        table_code = client.TABELAS["ppm_rebanho"]
        variable = client.VARIAVEIS_PPM["efetivo"]
        classifications["79"] = client.REBANHOS_PPM[especie_lower]
    else:
        table_code = client.TABELAS["ppm_producao"]
        variable = client.VARIAVEIS_PPM["producao"]
        classifications["80"] = client.PRODUTOS_ORIGEM_ANIMAL[especie_lower]

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=variable,
        period=period,
        classifications=classifications,
    )

    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "ano_cod",
            "D2N": "ano",
            "D3C": "variavel_cod",
            "D3N": "variavel",
            "D4C": "especie_cod",
            "D4N": "especie_raw",
        },
    )

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    df["especie"] = especie_lower
    df["unidade"] = client.UNIDADES_PPM.get(especie_lower, "")
    df["fonte"] = "ibge_ppm"

    output_cols = [
        c
        for c in [
            "ano",
            "localidade",
            "localidade_cod",
            "especie",
            "valor",
            "unidade",
            "fonte",
        ]
        if c in df.columns
    ]
    df = df[output_cols].reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:ppm",
        {"especie": especie, "ano": ano},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "ppm")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_ppm_success",
        especie=especie,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


@overload
async def abate(
    especie: str,
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def abate(
    especie: str,
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def abate(
    especie: str,
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_abate",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_abate_request",
        especie=especie,
        trimestre=trimestre,
        uf=uf,
    )

    especie_lower = especie.lower()
    if especie_lower not in client.ESPECIES_ABATE:
        raise ValueError(f"Espécie não suportada: {especie}. Disponíveis: {client.ESPECIES_ABATE}")

    table_code = client.TABELAS_ABATE[especie_lower]
    var_codes = ",".join(client.VARIAVEIS_ABATE.values())

    territorial_level = "3" if uf is None else "3"
    ibge_code = "all"
    if uf:
        ibge_code = client.uf_to_ibge_code(uf)

    if trimestre is None:
        period = "last"
    elif isinstance(trimestre, list):
        period = ",".join(str(t) for t in trimestre)
    else:
        period = str(trimestre)

    classifications: dict[str, str | list[str]] = {
        "12716": "115236",
        "12529": "118225",
    }
    if especie_lower == "bovino":
        classifications["18"] = "992"

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=var_codes,
        period=period,
        classifications=classifications,
    )

    col_map = {
        "NC": "nivel_cod",
        "NN": "nivel",
        "MC": "unidade_cod",
        "MN": "unidade",
        "V": "valor",
        "D1C": "localidade_cod",
        "D1N": "localidade",
    }

    trimestre_col = None
    variavel_col = None
    variavel_name_col = ""
    trimestre_name_col = ""
    var_ids = {"284", "285", "1000284", "1000285", "151", "1000151"}
    for dc in ["D2C", "D3C"]:
        if dc not in df.columns or len(df) == 0:
            continue
        sample_str = str(df[dc].iloc[0])
        name_col = dc[:-1] + "N"
        if sample_str in var_ids:
            variavel_col = dc
            variavel_name_col = name_col
        elif len(sample_str) == 6 and sample_str[:4].isdigit():
            trimestre_col = dc
            trimestre_name_col = name_col

    if variavel_col:
        col_map[variavel_col] = "variavel_cod"
        col_map[variavel_name_col] = "variavel_nome"
    if trimestre_col:
        col_map[trimestre_col] = "trimestre_cod"
        col_map[trimestre_name_col] = "trimestre_nome"

    rename_map = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    if "trimestre_cod" in df.columns:
        df["trimestre"] = df["trimestre_cod"].astype(str)

    cabecas = df[df["variavel_cod"].astype(str) == "284"].copy()
    peso = df[df["variavel_cod"].astype(str) == "285"].copy()

    merge_keys = [c for c in ["trimestre", "localidade", "localidade_cod"] if c in cabecas.columns]

    if not cabecas.empty and not peso.empty and merge_keys:
        cabecas = cabecas.rename(columns={"valor": "animais_abatidos"})
        peso = peso.rename(columns={"valor": "peso_carcacas"})
        result = cabecas[merge_keys + ["animais_abatidos"]].merge(
            peso[merge_keys + ["peso_carcacas"]],
            on=merge_keys,
            how="outer",
        )
    elif not cabecas.empty:
        result = cabecas.rename(columns={"valor": "animais_abatidos"})
        result["peso_carcacas"] = pd.NA
    else:
        result = pd.DataFrame()

    if not result.empty:
        if "localidade_cod" in result.columns:
            result["localidade_cod"] = pd.to_numeric(
                result["localidade_cod"], errors="coerce"
            ).astype("Int64")

        result["especie"] = especie_lower
        result["fonte"] = "ibge_abate"

        output_cols = [
            c
            for c in [
                "trimestre",
                "localidade",
                "localidade_cod",
                "especie",
                "animais_abatidos",
                "peso_carcacas",
                "fonte",
            ]
            if c in result.columns
        ]
        result = result[output_cols].reset_index(drop=True)

        for col in ["animais_abatidos", "peso_carcacas"]:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce")

    df = result

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:abate",
        {"especie": especie, "trimestre": trimestre},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "abate")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_abate_success",
        especie=especie,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


async def especies_abate() -> list[str]:
    return list(client.ESPECIES_ABATE)


async def especies_ppm() -> list[str]:
    return sorted(list(client.REBANHOS_PPM.keys()) + list(client.PRODUTOS_ORIGEM_ANIMAL.keys()))


_CLASSIFICACOES_CENSO_AGRO: dict[tuple[str, str], dict[str, str]] = {
    ("efetivo_rebanho", "1995"): {"224": "all", "220": "0"},
    ("uso_terra", "1995"): {"222": "all", "220": "0"},
    ("lavoura_temporaria", "1995"): {"226": "all", "220": "0"},
    ("lavoura_permanente", "1995"): {"227": "all", "220": "0"},
    ("efetivo_rebanho", "2017"): {
        "829": "46302",
        "12443": "all",
        "218": "46502",
    },
    ("uso_terra", "2017"): {
        "829": "46302",
        "222": "all",
        "218": "46502",
        "12517": "113601",
        "12567": "41151",
    },
    ("lavoura_temporaria", "2017"): {
        "829": "46302",
        "226": "all",
        "218": "46502",
        "12517": "113601",
    },
    ("lavoura_permanente", "2017"): {
        "829": "46302",
        "227": "all",
        "220": "110085",
    },
    ("preparo_solo", "2006"): {
        "12585": "all",
    },
    ("preparo_solo", "2017"): {
        "829": "46302",
        "12564": "41145",
        "12771": "45951",
        "218": "46502",
    },
    ("adubacao", "2006"): {
        "12586": "all",
    },
    ("adubacao", "2017"): {
        "12522": "all",
    },
    ("calagem", "2006"): {
        "12549": "all",
    },
    ("calagem", "2017"): {
        "12549": "all",
    },
    ("agrotoxicos", "2006"): {
        "12521": "all",
    },
    ("agrotoxicos", "2017"): {
        "12521": "all",
    },
    ("praticas_agricolas", "2006"): {
        "12568": "all",
    },
    ("praticas_agricolas", "2017"): {
        "12568": "all",
    },
    ("irrigacao", "2006"): {
        "12604": "all",
    },
    ("irrigacao", "2017"): {
        "12604": "all",
    },
}

_CENSO_VAR_NOME: dict[str, str] = {
    "105": "cabecas",
    "151": "estabelecimentos",
    "214": "producao",
    "216": "area_colhida",
    "10010": "estabelecimentos",
    "2209": "cabecas",
    "9587": "estabelecimentos",
    "184": "area",
    "183": "estabelecimentos",
    "10084": "estabelecimentos",
    "10085": "producao",
    "10089": "area_colhida",
    "9504": "estabelecimentos",
    "9506": "producao",
    "10078": "area_colhida",
}

_CENSO_VAR_UNIDADE: dict[str, str] = {
    "105": "cabeças",
    "151": "unidades",
    "214": "",
    "216": "hectares",
    "10010": "unidades",
    "2209": "cabeças",
    "9587": "unidades",
    "184": "hectares",
    "183": "unidades",
    "10084": "unidades",
    "10085": "",
    "10089": "hectares",
    "9504": "unidades",
    "9506": "",
    "10078": "hectares",
}

_CENSO_ALL_VAR_IDS: set[str] = set(_CENSO_VAR_NOME.keys())

_CENSO_CATEGORIA_COL_INDEX: dict[tuple[str, str], int] = {
    ("efetivo_rebanho", "1995"): 3,
    ("uso_terra", "1995"): 3,
    ("lavoura_temporaria", "1995"): 3,
    ("lavoura_permanente", "1995"): 3,
    ("efetivo_rebanho", "2017"): 5,
    ("uso_terra", "2017"): 5,
    ("lavoura_temporaria", "2017"): 5,
    ("lavoura_permanente", "2017"): 5,
    ("preparo_solo", "2006"): 3,
    ("adubacao", "2006"): 3,
    ("adubacao", "2017"): 3,
    ("calagem", "2006"): 3,
    ("calagem", "2017"): 3,
    ("agrotoxicos", "2006"): 3,
    ("agrotoxicos", "2017"): 3,
    ("praticas_agricolas", "2006"): 3,
    ("praticas_agricolas", "2017"): 3,
    ("irrigacao", "2006"): 3,
    ("irrigacao", "2017"): 3,
}

_VAR_AS_CATEGORIA: dict[tuple[str, str], dict[str, tuple[str, str, str]]] = {
    ("preparo_solo", "2017"): {
        "9562": ("Não utiliza preparo", "estabelecimentos", "unidades"),
        "9563": ("Utiliza preparo", "estabelecimentos", "unidades"),
        "9564": ("Cultivo convencional", "estabelecimentos", "unidades"),
        "9565": ("Cultivo mínimo", "estabelecimentos", "unidades"),
        "2016": ("Plantio direto na palha", "estabelecimentos", "unidades"),
        "2018": ("Plantio direto na palha", "area", "hectares"),
    },
}

_CENSO_MULTI_TABLE: dict[tuple[str, str], list[tuple[str, dict[str, str]]]] = {
    ("uso_terra", "1995"): [
        ("316", {"area": "184"}),
        ("311", {"estabelecimentos": "183"}),
    ],
    ("lavoura_temporaria", "1995"): [
        ("497", {"producao": "214"}),
        ("492", {"estabelecimentos": "151"}),
        ("503", {"area_colhida": "216"}),
    ],
    ("lavoura_permanente", "1995"): [
        ("509", {"producao": "214"}),
        ("504", {"estabelecimentos": "151"}),
        ("510", {"area_colhida": "216"}),
    ],
}


def _empty_censo_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "ano",
            "localidade",
            "localidade_cod",
            "tema",
            "categoria",
            "variavel",
            "valor",
            "unidade",
            "fonte",
        ]
    )


def _parse_censo_raw(
    df: pd.DataFrame,
    tema: str,
    ano_key: str,
    var_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    key = (tema, ano_key)

    vac = _VAR_AS_CATEGORIA.get(key)
    if vac:
        return _process_var_as_categoria(df, tema, ano_key, vac)

    col_map: dict[str, str] = {
        "NC": "nivel_cod",
        "NN": "nivel",
        "V": "valor",
        "D1C": "localidade_cod",
        "D1N": "localidade",
    }

    for dc in ["D2C", "D3C"]:
        if dc not in df.columns or len(df) == 0:
            continue
        sample = str(df[dc].iloc[0])
        name_col = dc[:-1] + "N"
        if sample in _CENSO_ALL_VAR_IDS:
            col_map[dc] = "variavel_cod"
            col_map[name_col] = "variavel_nome"
        elif len(sample) == 4 and sample.isdigit():
            col_map[dc] = "ano_cod"
            col_map[name_col] = "ano_nome"

    cat_idx = _CENSO_CATEGORIA_COL_INDEX.get(key)
    if cat_idx:
        cat_col_c = f"D{cat_idx}C"
        cat_col_n = f"D{cat_idx}N"
        if cat_col_c in col_map:
            for i in range(2, 7):
                alt_c = f"D{i}C"
                if alt_c in df.columns and alt_c not in col_map:
                    cat_col_c = alt_c
                    cat_col_n = f"D{i}N"
                    break
        if cat_col_c in df.columns and cat_col_c not in col_map:
            col_map[cat_col_c] = "categoria_cod"
        if cat_col_n in df.columns and cat_col_n not in col_map:
            col_map[cat_col_n] = "categoria"

    rename_map = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    if "categoria" in df.columns:
        df = df[df["categoria"].str.lower() != "total"]

    if "ano_cod" in df.columns:
        df["ano"] = pd.to_numeric(df["ano_cod"], errors="coerce").astype("Int64")
    else:
        df["ano"] = int(ano_key)

    if "variavel_cod" in df.columns:
        df["variavel"] = df["variavel_cod"].map(_CENSO_VAR_NOME).fillna(df.get("variavel_nome", ""))
        unidade_from_map = df["variavel_cod"].map(_CENSO_VAR_UNIDADE)
        mn_col = "MN" if "MN" in df.columns else None
        if mn_col is None:
            for c in df.columns:
                if c == "MN":
                    mn_col = c
                    break
        if mn_col and mn_col in df.columns:
            df["unidade"] = unidade_from_map.where(unidade_from_map != "", df[mn_col])
        else:
            df["unidade"] = unidade_from_map.fillna("")
    else:
        effective_var_map = var_map or client.VARIAVEIS_CENSO_AGRO.get(tema, {}).get(ano_key, {})
        if len(effective_var_map) == 1:
            var_name = next(iter(effective_var_map))
            var_code = next(iter(effective_var_map.values()))
            df["variavel"] = var_name
            df["unidade"] = _CENSO_VAR_UNIDADE.get(var_code, "")
        else:
            df["variavel"] = ""
            df["unidade"] = ""

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    df["tema"] = tema
    df["fonte"] = "ibge_censo_agro"

    output_cols = [
        c
        for c in [
            "ano",
            "localidade",
            "localidade_cod",
            "tema",
            "categoria",
            "variavel",
            "valor",
            "unidade",
            "fonte",
        ]
        if c in df.columns
    ]
    return df[output_cols].reset_index(drop=True)


async def _fetch_censo_multi_table(
    tema: str,
    ano_key: str,
    table_specs: list[tuple[str, dict[str, str]]],
    territorial_level: str,
    ibge_code: str,
) -> pd.DataFrame:
    key = (tema, ano_key)
    classifications: dict[str, str | list[str]] = dict(_CLASSIFICACOES_CENSO_AGRO.get(key, {}))
    frames: list[pd.DataFrame] = []

    for table_code, var_map in table_specs:
        var_codes = ",".join(var_map.values())
        df = await client.fetch_sidra(
            table_code=table_code,
            territorial_level=territorial_level,
            ibge_territorial_code=ibge_code,
            variable=var_codes,
            period="all",
            classifications=classifications,
        )
        if df.empty:
            continue
        parsed = _parse_censo_raw(df, tema, ano_key, var_map=var_map)
        if not parsed.empty:
            frames.append(parsed)

    if not frames:
        return _empty_censo_df()
    return pd.concat(frames, ignore_index=True)


async def _fetch_censo_single(
    tema: str,
    ano_key: str,
    territorial_level: str,
    ibge_code: str,
) -> pd.DataFrame:
    key = (tema, ano_key)

    multi_spec = _CENSO_MULTI_TABLE.get(key)
    if multi_spec:
        return await _fetch_censo_multi_table(
            tema, ano_key, multi_spec, territorial_level, ibge_code
        )

    table_code = client.TABELAS_CENSO_AGRO[tema][ano_key]
    var_map = client.VARIAVEIS_CENSO_AGRO[tema][ano_key]
    var_codes = ",".join(var_map.values())
    classifications: dict[str, str | list[str]] = dict(_CLASSIFICACOES_CENSO_AGRO.get(key, {}))

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=var_codes,
        period="all",
        classifications=classifications,
    )

    if df.empty:
        return _empty_censo_df()

    return _parse_censo_raw(df, tema, ano_key)


def _process_var_as_categoria(
    df: pd.DataFrame,
    tema: str,
    ano_key: str,
    vac: dict[str, tuple[str, str, str]],
) -> pd.DataFrame:
    col_map: dict[str, str] = {
        "NC": "nivel_cod",
        "NN": "nivel",
        "V": "valor",
        "D1C": "localidade_cod",
        "D1N": "localidade",
    }

    var_col = None
    for dc in ["D2C", "D3C"]:
        if dc not in df.columns or len(df) == 0:
            continue
        sample = str(df[dc].iloc[0])
        name_col = dc[:-1] + "N"
        if sample in vac:
            var_col = dc
            col_map[dc] = "variavel_cod"
            col_map[name_col] = "variavel_nome"
        elif len(sample) == 4 and sample.isdigit():
            col_map[dc] = "ano_cod"
            col_map[name_col] = "ano_nome"

    if var_col is None:
        for dc in ["D2C", "D3C"]:
            if dc not in df.columns:
                continue
            if df[dc].iloc[0] in vac:
                var_col = dc
                name_col = dc[:-1] + "N"
                col_map[dc] = "variavel_cod"
                col_map[name_col] = "variavel_nome"
                break

    rename_map = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    df["ano"] = int(ano_key)

    if "variavel_cod" in df.columns:
        df["categoria"] = df["variavel_cod"].map(lambda v: vac.get(str(v), ("", "", ""))[0])
        df["variavel"] = df["variavel_cod"].map(lambda v: vac.get(str(v), ("", "", ""))[1])
        df["unidade"] = df["variavel_cod"].map(lambda v: vac.get(str(v), ("", "", ""))[2])
        df = df[df["categoria"] != ""]
    else:
        df["categoria"] = ""
        df["variavel"] = ""
        df["unidade"] = ""

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    df["tema"] = tema
    df["fonte"] = "ibge_censo_agro"

    output_cols = [
        c
        for c in [
            "ano",
            "localidade",
            "localidade_cod",
            "tema",
            "categoria",
            "variavel",
            "valor",
            "unidade",
            "fonte",
        ]
        if c in df.columns
    ]
    return df[output_cols].reset_index(drop=True)


@overload
async def censo_agro(
    tema: str,
    ano: int | str | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def censo_agro(
    tema: str,
    ano: int | str | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def censo_agro(
    tema: str,
    ano: int | str | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_censo_agro",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_censo_agro_request",
        tema=tema,
        ano=ano,
        uf=uf,
        nivel=nivel,
    )

    tema_lower = tema.lower()
    if tema_lower not in client.TABELAS_CENSO_AGRO:
        raise ValueError(f"Tema não suportado: {tema}. Disponíveis: {client.TEMAS_CENSO_AGRO}")

    anos_disponiveis = list(client.TABELAS_CENSO_AGRO[tema_lower].keys())

    if ano is not None:
        ano_str = str(ano)
        if ano_str not in anos_disponiveis:
            raise ValueError(
                f"Ano {ano} não disponível para tema '{tema_lower}'. Disponíveis: {anos_disponiveis}"
            )
        anos_fetch = [ano_str]
    else:
        anos_fetch = anos_disponiveis

    nivel_map = {
        "brasil": "1",
        "uf": "3",
        "municipio": "6",
    }
    territorial_level = nivel_map.get(nivel, "3")

    ibge_code = "all"
    if uf:
        uf_ibge = client.uf_to_ibge_code(uf)
        if nivel == "municipio":
            ibge_code = f"in N3 {uf_ibge}"
        elif nivel == "uf":
            ibge_code = uf_ibge

    frames: list[pd.DataFrame] = []
    for ano_key in anos_fetch:
        sub_df = await _fetch_censo_single(tema_lower, ano_key, territorial_level, ibge_code)
        if not sub_df.empty:
            frames.append(sub_df)

    df = pd.concat(frames, ignore_index=True) if frames else _empty_censo_df()

    if not df.empty and "ano" in df.columns and "localidade" in df.columns:
        df = df.sort_values(["ano", "localidade"]).reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:censo_agro",
        {"tema": tema, "ano": ano, "uf": uf},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "censo_agro")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_censo_agro_success",
        tema=tema,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


async def temas_censo_agro() -> list[str]:
    return list(client.TEMAS_CENSO_AGRO)


def _parse_censo_historico_raw(df: pd.DataFrame, tema: str) -> pd.DataFrame:
    if df.empty:
        return _empty_censo_df()

    periodos_set = {str(p) for p in client.PERIODOS_CENSO_HISTORICO[tema]}
    var_codes_set = set(client.VARIAVEIS_CENSO_HISTORICO[tema].values())
    reverse_vars = {v: k for k, v in client.VARIAVEIS_CENSO_HISTORICO[tema].items()}
    categorias = client.CATEGORIAS_CENSO_HISTORICO.get(tema, {})
    has_classification = bool(client.CLASSIFICACOES_CENSO_HISTORICO[tema])

    ano_dc = var_dc = cat_dc = None
    for dc in ["D2C", "D3C", "D4C"]:
        if dc not in df.columns:
            continue
        sample = str(df[dc].iloc[0])
        if ano_dc is None and re.fullmatch(r"\d{4}", sample) and sample in periodos_set:
            ano_dc = dc
        elif var_dc is None and sample in var_codes_set:
            var_dc = dc
        elif cat_dc is None:
            cat_dc = dc

    result = pd.DataFrame()
    result["localidade"] = df["D1N"].values
    result["localidade_cod"] = pd.to_numeric(df["D1C"], errors="coerce").astype("Int64")

    if ano_dc:
        result["ano"] = pd.to_numeric(df[ano_dc], errors="coerce").astype("Int64")

    if var_dc:
        vc = df[var_dc].astype(str)
        result["variavel"] = vc.map(reverse_vars).fillna(vc)
    elif len(var_codes_set) == 1:
        code = next(iter(var_codes_set))
        result["variavel"] = reverse_vars.get(code, code)
        vc = pd.Series(code, index=df.index)
    else:
        result["variavel"] = ""
        vc = pd.Series("", index=df.index)

    if cat_dc:
        cc = df[cat_dc].astype(str)
        cat_name_col = cat_dc[:-1] + "N"
        mapped = cc.map(categorias)
        if cat_name_col in df.columns:
            result["categoria"] = mapped.fillna(df[cat_name_col])
        else:
            result["categoria"] = mapped.fillna("")
    elif not has_classification:
        result["categoria"] = "total"
        cc = pd.Series("", index=df.index)
    else:
        result["categoria"] = ""
        cc = pd.Series("", index=df.index)

    fixed_unit = vc.map(client.UNIDADES_VARIAVEIS_CENSO_HISTORICO)
    if cat_dc:
        cat_unit = cc.map(client.UNIDADES_CATEGORIAS_CENSO_HISTORICO)
    else:
        cat_unit = pd.Series(pd.NA, index=df.index)
    mn_unit = df["MN"] if "MN" in df.columns else pd.Series("", index=df.index)
    result["unidade"] = fixed_unit.fillna(cat_unit).fillna(mn_unit).fillna("")

    result["valor"] = pd.to_numeric(df["V"], errors="coerce")
    result["tema"] = tema
    result["fonte"] = "ibge_censo_agro_historico"

    output_cols = [
        "ano",
        "localidade",
        "localidade_cod",
        "tema",
        "categoria",
        "variavel",
        "valor",
        "unidade",
        "fonte",
    ]
    return result[output_cols].reset_index(drop=True)


@overload
async def censo_agro_historico(
    tema: str,
    ano: int | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "regiao", "uf"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def censo_agro_historico(
    tema: str,
    ano: int | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "regiao", "uf"] = "uf",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def censo_agro_historico(
    tema: str,
    ano: int | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "regiao", "uf"] = "uf",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_censo_agro_historico",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_censo_agro_historico_request",
        tema=tema,
        ano=ano,
        uf=uf,
        nivel=nivel,
    )

    tema_lower = tema.lower()
    if tema_lower not in client.TABELAS_CENSO_HISTORICO:
        raise ValueError(f"Tema não suportado: {tema}. Disponíveis: {client.TEMAS_CENSO_HISTORICO}")

    niveis_validos = client.NIVEIS_CENSO_HISTORICO[tema_lower]
    if nivel not in niveis_validos:
        raise ValueError(
            f"Nível '{nivel}' não disponível para tema '{tema_lower}'. "
            f"Disponíveis: {niveis_validos}"
        )

    periodos = client.PERIODOS_CENSO_HISTORICO[tema_lower]
    if ano is None:
        anos = periodos
    elif isinstance(ano, int):
        if ano not in periodos:
            raise ValueError(
                f"Ano {ano} não disponível para tema '{tema_lower}'. Disponíveis: {periodos}"
            )
        anos = [ano]
    else:
        for a in ano:
            if a not in periodos:
                raise ValueError(
                    f"Ano {a} não disponível para tema '{tema_lower}'. Disponíveis: {periodos}"
                )
        anos = ano

    nivel_map = {"brasil": "1", "regiao": "2", "uf": "3"}
    territorial_level = nivel_map[nivel]

    ibge_code = "all"
    if uf and nivel == "uf":
        ibge_code = client.uf_to_ibge_code(uf)

    period = ",".join(str(a) for a in anos)
    variable = ",".join(client.VARIAVEIS_CENSO_HISTORICO[tema_lower].values())
    classifications: dict[str, str | list[str]] | None = (
        dict(client.CLASSIFICACOES_CENSO_HISTORICO[tema_lower]) or None
    )

    df = await client.fetch_sidra(
        table_code=client.TABELAS_CENSO_HISTORICO[tema_lower],
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=variable,
        period=period,
        classifications=classifications,
    )

    df = _empty_censo_df() if df.empty else _parse_censo_historico_raw(df, tema_lower)

    if not df.empty and "ano" in df.columns and "localidade" in df.columns:
        df = df.sort_values(["ano", "localidade"]).reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:censo_agro_historico",
        {"tema": tema, "ano": ano, "uf": uf},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.IBGE, "censo_agro")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info(
        "ibge_censo_agro_historico_success",
        tema=tema,
        records=len(df),
    )

    if return_meta:
        return df, meta
    return df


async def temas_censo_agro_historico() -> list[str]:
    return list(client.TEMAS_CENSO_HISTORICO)


async def ufs() -> list[str]:
    return list(client.get_uf_codes().keys())


# ---------------------------------------------------------------------------
# Silvicultura (PEVS) — tab 291 (produção c194) + tab 5930 (área c734)
# ---------------------------------------------------------------------------


@overload
async def silvicultura(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def silvicultura(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def silvicultura(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_silvicultura",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_silvicultura_request",
        produto=produto,
        ano=ano,
        uf=uf,
        nivel=nivel,
        variavel=variavel,
    )

    produto_lower = produto.lower()
    variavel_lower = variavel.lower()

    if variavel_lower == "area":
        if produto_lower not in client.ESPECIES_SILVICULTURA_AREA:
            raise ValueError(
                f"Espécie não suportada para área: {produto}. "
                f"Disponíveis: {list(client.ESPECIES_SILVICULTURA_AREA.keys())}"
            )
        table_code = client.TABELAS_PEVS["silvicultura_area"]
        var_code = client.VARIAVEIS_SILVICULTURA_AREA["area_total"]
        classification_key = "734"
        classification_val = client.ESPECIES_SILVICULTURA_AREA[produto_lower]
    elif variavel_lower in ("quantidade_produzida", "valor_producao"):
        if produto_lower not in client.PRODUTOS_SILVICULTURA:
            raise ValueError(
                f"Produto não suportado: {produto}. "
                f"Disponíveis: {list(client.PRODUTOS_SILVICULTURA.keys())}"
            )
        table_code = client.TABELAS_PEVS["silvicultura_producao"]
        var_code = client.VARIAVEIS_SILVICULTURA[variavel_lower]
        classification_key = "194"
        classification_val = client.PRODUTOS_SILVICULTURA[produto_lower]
    else:
        raise ValueError(
            f"Variável não suportada: {variavel}. "
            f"Disponíveis: ['quantidade_produzida', 'valor_producao', 'area']"
        )

    nivel_map = {"brasil": "1", "uf": "3", "municipio": "6"}
    territorial_level = nivel_map.get(nivel, "3")

    ibge_code = "all"
    if uf:
        uf_ibge = client.uf_to_ibge_code(uf)
        if nivel == "municipio":
            ibge_code = f"in N3 {uf_ibge}"
        elif nivel == "uf":
            ibge_code = uf_ibge

    if ano is None:
        period = "last"
    elif isinstance(ano, list):
        period = ",".join(str(a) for a in ano)
    else:
        period = str(ano)

    classifications: dict[str, str | list[str]] = {classification_key: classification_val}

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=var_code,
        period=period,
        classifications=classifications,
    )

    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "ano_cod",
            "D2N": "ano",
            "D3C": "variavel_cod",
            "D3N": "variavel_nome",
            "D4C": "produto_cod",
            "D4N": "produto_raw",
        },
    )

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    df["produto"] = produto_lower
    if variavel_lower == "area":
        df["unidade"] = "Hectares"
    else:
        df["unidade"] = client.UNIDADES_SILVICULTURA.get(produto_lower, "")
    df["fonte"] = "ibge_silvicultura"

    output_cols = [
        c
        for c in ["ano", "localidade", "localidade_cod", "produto", "valor", "unidade", "fonte"]
        if c in df.columns
    ]
    df = df[output_cols].reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:silvicultura",
        {"produto": produto, "ano": ano, "variavel": variavel},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry("ibge_silvicultura")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info("ibge_silvicultura_success", produto=produto, records=len(df))

    if return_meta:
        return df, meta
    return df


async def produtos_silvicultura() -> list[str]:
    return list(client.PRODUTOS_SILVICULTURA.keys())


async def especies_silvicultura_area() -> list[str]:
    return list(client.ESPECIES_SILVICULTURA_AREA.keys())


# ---------------------------------------------------------------------------
# Extração Vegetal (PEVS) — tab 289 (c193)
# ---------------------------------------------------------------------------


@overload
async def extracao_vegetal(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def extracao_vegetal(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def extracao_vegetal(
    produto: str,
    ano: int | str | list[int] | None = None,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    variavel: str = "quantidade_produzida",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_extracao_vegetal",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_extracao_vegetal_request",
        produto=produto,
        ano=ano,
        uf=uf,
        nivel=nivel,
        variavel=variavel,
    )

    produto_lower = produto.lower()
    variavel_lower = variavel.lower()

    if produto_lower not in client.PRODUTOS_EXTRACAO_VEGETAL:
        raise ValueError(
            f"Produto não suportado: {produto}. "
            f"Disponíveis: {list(client.PRODUTOS_EXTRACAO_VEGETAL.keys())}"
        )

    if variavel_lower not in client.VARIAVEIS_EXTRACAO_VEGETAL:
        raise ValueError(
            f"Variável não suportada: {variavel}. "
            f"Disponíveis: {list(client.VARIAVEIS_EXTRACAO_VEGETAL.keys())}"
        )

    table_code = client.TABELAS_PEVS["extracao_vegetal"]
    var_code = client.VARIAVEIS_EXTRACAO_VEGETAL[variavel_lower]
    produto_cod = client.PRODUTOS_EXTRACAO_VEGETAL[produto_lower]

    nivel_map = {"brasil": "1", "uf": "3", "municipio": "6"}
    territorial_level = nivel_map.get(nivel, "3")

    ibge_code = "all"
    if uf:
        uf_ibge = client.uf_to_ibge_code(uf)
        if nivel == "municipio":
            ibge_code = f"in N3 {uf_ibge}"
        elif nivel == "uf":
            ibge_code = uf_ibge

    if ano is None:
        period = "last"
    elif isinstance(ano, list):
        period = ",".join(str(a) for a in ano)
    else:
        period = str(ano)

    classifications: dict[str, str | list[str]] = {"193": produto_cod}

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=var_code,
        period=period,
        classifications=classifications,
    )

    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "ano_cod",
            "D2N": "ano",
            "D3C": "variavel_cod",
            "D3N": "variavel_nome",
            "D4C": "produto_cod",
            "D4N": "produto_raw",
        },
    )

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    df["produto"] = produto_lower
    df["unidade"] = client.UNIDADES_EXTRACAO_VEGETAL.get(produto_lower, "")
    df["fonte"] = "ibge_extracao_vegetal"

    output_cols = [
        c
        for c in ["ano", "localidade", "localidade_cod", "produto", "valor", "unidade", "fonte"]
        if c in df.columns
    ]
    df = df[output_cols].reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:extracao_vegetal",
        {"produto": produto, "ano": ano, "variavel": variavel},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry("ibge_extracao_vegetal")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info("ibge_extracao_vegetal_success", produto=produto, records=len(df))

    if return_meta:
        return df, meta
    return df


async def produtos_extracao_vegetal() -> list[str]:
    return list(client.PRODUTOS_EXTRACAO_VEGETAL.keys())


# ---------------------------------------------------------------------------
# Leite Trimestral — tab 1086
# ---------------------------------------------------------------------------


@overload
async def leite_trimestral(
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def leite_trimestral(
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def leite_trimestral(
    trimestre: str | list[str] | None = None,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_leite_trimestral",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_leite_trimestral_request",
        trimestre=trimestre,
        uf=uf,
    )

    table_code = client.TABELAS_LEITE["leite_trimestral"]
    var_codes = list(client.VARIAVEIS_LEITE.values())

    territorial_level = "3"
    ibge_code = "all"
    if uf:
        ibge_code = client.uf_to_ibge_code(uf)

    if trimestre is None:
        period = "last"
    elif isinstance(trimestre, list):
        period = ",".join(str(t) for t in trimestre)
    else:
        period = str(trimestre)

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level=territorial_level,
        ibge_territorial_code=ibge_code,
        variable=var_codes,
        period=period,
    )

    # D1=localidade, D2=trimestre, D3=variável for tab 1086
    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "trimestre_cod",
            "D2N": "trimestre_nome",
            "D3C": "variavel_cod",
            "D3N": "variavel_nome",
        },
    )

    if "trimestre_cod" in df.columns:
        df["trimestre"] = df["trimestre_cod"].astype(str)

    if "localidade_cod" in df.columns:
        df["localidade_cod"] = pd.to_numeric(df["localidade_cod"], errors="coerce").astype("Int64")

    # Pivot: variavel_cod → wide columns
    var_name_map = {v: k for k, v in client.VARIAVEIS_LEITE.items()}
    merge_keys = [c for c in ["trimestre", "localidade", "localidade_cod"] if c in df.columns]

    pivot_frames = []
    for var_code, col_name in var_name_map.items():
        subset = df[df["variavel_cod"].astype(str) == var_code].copy()
        if subset.empty:
            continue
        subset = subset.rename(columns={"valor": col_name})
        subset = subset[merge_keys + [col_name]]
        pivot_frames.append(subset)

    if pivot_frames:
        result = pivot_frames[0]
        for pf in pivot_frames[1:]:
            result = result.merge(pf, on=merge_keys, how="outer")
    else:
        result = pd.DataFrame()

    if not result.empty:
        result["fonte"] = "ibge_leite_trimestral"

        for col in ["leite_adquirido", "leite_industrializado", "preco_medio"]:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce")

        output_cols = [
            c
            for c in [
                "trimestre",
                "localidade",
                "localidade_cod",
                "leite_adquirido",
                "leite_industrializado",
                "preco_medio",
                "fonte",
            ]
            if c in result.columns
        ]
        result = result[output_cols].reset_index(drop=True)

    df = result

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:leite_trimestral",
        {"trimestre": trimestre},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry("ibge_leite_trimestral")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info("ibge_leite_trimestral_success", records=len(df))

    if return_meta:
        return df, meta
    return df


# ---------------------------------------------------------------------------
# PIB Agro — tab 1846 (corrente) / 6612 (real)
# ---------------------------------------------------------------------------


@overload
async def pib_agro(
    trimestre: str | list[str] | None = None,
    precos: str = "corrente",
    setor: str = "agropecuaria",
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def pib_agro(
    trimestre: str | list[str] | None = None,
    precos: str = "corrente",
    setor: str = "agropecuaria",
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def pib_agro(
    trimestre: str | list[str] | None = None,
    precos: str = "corrente",
    setor: str = "agropecuaria",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    fetch_start = time.perf_counter()
    meta = MetaInfo(
        source="ibge_pib",
        source_url="https://sidra.ibge.gov.br",
        source_method="httpx",
        fetched_at=datetime.now(),
    )
    logger.info(
        "ibge_pib_agro_request",
        trimestre=trimestre,
        precos=precos,
        setor=setor,
    )

    precos_lower = precos.lower()
    setor_lower = setor.lower()

    if precos_lower not in client.VARIAVEIS_PIB:
        raise ValueError(
            f"Tipo de preços não suportado: {precos}. "
            f"Disponíveis: {list(client.VARIAVEIS_PIB.keys())}"
        )

    if setor_lower not in client.SETORES_PIB:
        raise ValueError(
            f"Setor não suportado: {setor}. Disponíveis: {list(client.SETORES_PIB.keys())}"
        )

    if precos_lower == "corrente":
        table_code = client.TABELAS_PIB["pib_corrente"]
    else:
        table_code = client.TABELAS_PIB["pib_real"]

    var_code = client.VARIAVEIS_PIB[precos_lower]
    setor_cod = client.SETORES_PIB[setor_lower]

    if trimestre is None:
        period = "last"
    elif isinstance(trimestre, list):
        period = ",".join(str(t) for t in trimestre)
    else:
        period = str(trimestre)

    classifications: dict[str, str | list[str]] = {"11255": setor_cod}

    df = await client.fetch_sidra(
        table_code=table_code,
        territorial_level="1",
        ibge_territorial_code="all",
        variable=var_code,
        period=period,
        classifications=classifications,
    )

    # D1=localidade, D2=trimestre, D3=variável, D4=setor
    df = client.parse_sidra_response(
        df,
        rename_columns={
            "MC": "unidade_cod",
            "MN": "unidade_medida",
            "D1C": "localidade_cod",
            "D1N": "localidade",
            "D2C": "trimestre_cod",
            "D2N": "trimestre_nome",
            "D3C": "variavel_cod",
            "D3N": "variavel_nome",
            "D4C": "setor_cod",
            "D4N": "setor_raw",
        },
    )

    if "trimestre_cod" in df.columns:
        df["trimestre"] = df["trimestre_cod"].astype(str)

    if "unidade_medida" in df.columns:
        df["unidade"] = df["unidade_medida"]
    else:
        df["unidade"] = "R$ (milhões)" if precos_lower == "corrente" else "R$ de 1995 (milhões)"

    df["setor"] = setor_lower
    df["fonte"] = "ibge_pib"

    output_cols = [
        c for c in ["trimestre", "valor", "unidade", "setor", "fonte"] if c in df.columns
    ]
    df = df[output_cols].reset_index(drop=True)

    meta.fetch_duration_ms = int((time.perf_counter() - fetch_start) * 1000)
    meta.records_count = len(df)
    meta.columns = df.columns.tolist()
    meta.cache_key = build_cache_key(
        "ibge:pib_agro",
        {"trimestre": trimestre, "precos": precos, "setor": setor},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry("ibge_pib")

    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value,no-any-return]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    logger.info("ibge_pib_agro_success", records=len(df))

    if return_meta:
        return df, meta
    return df
