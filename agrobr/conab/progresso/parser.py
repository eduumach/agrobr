from __future__ import annotations

from datetime import datetime

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.normalize.numeric import safe_float
from agrobr.utils.io import open_excel_safe

from .models import (
    COLUNAS_SAIDA,
    estado_para_uf,
    parse_cultura_header,
    parse_operacao_header,
)

logger = structlog.get_logger()

PARSER_VERSION = 1


def _parse_pct(val: object) -> float | None:
    has_pct = isinstance(val, str) and "%" in val
    v = safe_float(val, strip="%")
    if v is not None and has_pct and v > 1:
        return v / 100.0
    return v


def _parse_date(val: object) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    return str(val).strip()


def _read_xlsx_sheet(data: bytes) -> pd.DataFrame:
    xls = open_excel_safe(
        data, source="conab_progresso", parser_version=PARSER_VERSION, engine="openpyxl"
    )

    target_sheet: str | None = None
    for name in xls.sheet_names:
        name_str = str(name)
        if "progresso" in name_str.lower():
            target_sheet = name_str
            break
    if target_sheet is None:
        target_sheet = str(xls.sheet_names[0]) if xls.sheet_names else None

    if target_sheet is None:
        raise ParseError(
            source="conab_progresso",
            parser_version=PARSER_VERSION,
            reason="Nenhuma sheet encontrada no XLSX",
        )

    try:
        df_raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
    except Exception as e:
        raise ParseError(
            source="conab_progresso",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler sheet '{target_sheet}': {e}",
        ) from e

    if df_raw.empty:
        raise ParseError(
            source="conab_progresso",
            parser_version=PARSER_VERSION,
            reason="Sheet vazia",
        )

    return df_raw


def _build_record(
    cultura: str,
    safra: str | None,
    operacao: str,
    uf: str,
    semana: str,
    vals: list[object],
) -> dict[str, object]:
    return {
        "cultura": cultura,
        "safra": safra,
        "operacao": operacao,
        "estado": uf,
        "semana_atual": semana,
        "pct_ano_anterior": _parse_pct(vals[2]),
        "pct_semana_anterior": _parse_pct(vals[3]),
        "pct_semana_atual": _parse_pct(vals[4]),
        "pct_media_5_anos": _parse_pct(vals[5]),
    }


def parse_progresso_xlsx(data: bytes) -> pd.DataFrame:
    df_raw = _read_xlsx_sheet(data)

    records: list[dict[str, object]] = []
    cultura_atual: str | None = None
    safra_atual: str | None = None
    operacao_atual: str | None = None
    semana_atual: str = ""
    in_data_rows = False
    ncols = len(df_raw.columns)

    for _, row in df_raw.iterrows():
        vals = [v if pd.notna(v) else None for v in row]
        while len(vals) < 6:
            vals.append(None)

        col_1 = str(vals[1]).strip() if vals[1] is not None else ""

        parsed_cultura = parse_cultura_header(col_1)
        if parsed_cultura:
            cultura_atual, safra_atual = parsed_cultura
            operacao_atual = None
            in_data_rows = False
            continue

        parsed_op = parse_operacao_header(col_1)
        if parsed_op:
            operacao_atual = parsed_op
            in_data_rows = False
            continue

        if col_1 == "Estado" and cultura_atual and operacao_atual:
            in_data_rows = False
            continue

        if col_1 == "" and vals[2] is not None and isinstance(vals[2], int):
            year_val = vals[2]
            if isinstance(year_val, int) and 2000 <= year_val <= 2100:
                continue

        date_vals = [vals[i] for i in range(2, min(5, ncols)) if vals[i] is not None]
        if date_vals and all(isinstance(d, datetime) for d in date_vals):
            semana_atual = _parse_date(date_vals[-1]) if date_vals else ""
            in_data_rows = True
            continue

        if not in_data_rows or not cultura_atual or not operacao_atual:
            continue

        estado_raw = col_1
        if not estado_raw:
            continue

        if estado_raw.startswith("*") or estado_raw.startswith("("):
            continue
        if "estados" in estado_raw.lower() or "brasil" in estado_raw.lower():
            records.append(
                _build_record(cultura_atual, safra_atual, operacao_atual, "BR", semana_atual, vals)
            )
            continue
        if estado_raw.lower().startswith("valores") or estado_raw.lower().startswith("percentual"):
            in_data_rows = False
            continue
        if estado_raw.lower().startswith("estimativa"):
            continue

        uf = estado_para_uf(estado_raw)
        records.append(
            _build_record(cultura_atual, safra_atual, operacao_atual, uf, semana_atual, vals)
        )

    if not records:
        raise ParseError(
            source="conab_progresso",
            parser_version=PARSER_VERSION,
            reason="Nenhum registro extraido do XLSX",
        )

    result = pd.DataFrame(records, columns=COLUNAS_SAIDA)
    logger.info("conab_progresso_parse_ok", records=len(result))
    return result
