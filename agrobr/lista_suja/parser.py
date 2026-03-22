from __future__ import annotations

import io
from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError

from .models import COLUNAS_SAIDA, PDF_HEADER_ROW_MARKER, RENAME_MAP

logger = structlog.get_logger()

PARSER_VERSION = 2


def _check_pdfplumber() -> Any:
    try:
        import pdfplumber

        return pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for lista_suja. Install with: pip install agrobr[pdf]"
        ) from None


def parse_empregadores(data: bytes) -> pd.DataFrame:
    pdfplumber = _check_pdfplumber()

    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as e:
        raise ParseError(
            source="lista_suja",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao abrir PDF: {e}",
        ) from e

    header: list[str] | None = None
    all_rows: list[list[str]] = []

    for page in pdf.pages:
        table = page.extract_table()
        if not table:
            continue
        for row in table:
            if not row or not row[0]:
                continue
            if row[0].strip() == PDF_HEADER_ROW_MARKER and header is None:
                header = [c.strip() if c else "" for c in row]
                continue
            if header and len(row) == len(header):
                all_rows.append(row)

    pdf.close()

    if not header or not all_rows:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    df = pd.DataFrame(all_rows, columns=header)

    rename_found = {k: v for k, v in RENAME_MAP.items() if k in df.columns}
    if not rename_found:
        raise ParseError(
            source="lista_suja",
            parser_version=PARSER_VERSION,
            reason=f"Nenhuma coluna esperada encontrada. Colunas: {df.columns.tolist()}",
        )

    df = df.rename(columns=rename_found)

    if "data_inclusao" in df.columns:
        df["data_inclusao"] = pd.to_datetime(df["data_inclusao"], errors="coerce", dayfirst=True)
    if "trabalhadores_resgatados" in df.columns:
        df["trabalhadores_resgatados"] = pd.to_numeric(
            df["trabalhadores_resgatados"], errors="coerce"
        )
    if "ano_acao_fiscal" in df.columns:
        df["ano_acao_fiscal"] = pd.to_numeric(df["ano_acao_fiscal"], errors="coerce")
    if "uf" in df.columns:
        df["uf"] = df["uf"].fillna("").str.strip().str.upper()

    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)

    logger.info("lista_suja_parse_ok", records=len(df))
    return df
