from __future__ import annotations

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.io import read_excel_safe

from .models import COLUNAS_SAIDA, RENAME_MAP

logger = structlog.get_logger()

PARSER_VERSION = 1


def parse_empregadores(data: bytes) -> pd.DataFrame:
    df = read_excel_safe(
        data,
        source="lista_suja",
        parser_version=PARSER_VERSION,
        label="Lista Suja XLSX",
    )

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    rename_found = {k: v for k, v in RENAME_MAP.items() if k in df.columns}
    if not rename_found:
        raise ParseError(
            source="lista_suja",
            parser_version=PARSER_VERSION,
            reason=f"Nenhuma coluna esperada encontrada. Colunas: {df.columns.tolist()}",
        )

    df = df.rename(columns=rename_found)

    if "data_inclusao" in df.columns:
        df["data_inclusao"] = pd.to_datetime(df["data_inclusao"], errors="coerce")
    if "trabalhadores_resgatados" in df.columns:
        df["trabalhadores_resgatados"] = pd.to_numeric(
            df["trabalhadores_resgatados"], errors="coerce"
        )
    if "uf" in df.columns:
        df["uf"] = df["uf"].fillna("").str.strip().str.upper()

    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)

    logger.info("lista_suja_parse_ok", records=len(df))
    return df
