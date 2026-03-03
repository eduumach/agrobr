from __future__ import annotations

from io import StringIO

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.normalize.encoding import detect_encoding_chain

from .models import COLUNAS_SAIDA, CULTURAS_ZARC

logger = structlog.get_logger()

PARSER_VERSION = 1

_RENAME_MAP = {
    "Nome_cultura": "cultura_raw",
    "Cod_Solo": "solo_codigo",
    "Cod_Ciclo": "ciclo_codigo",
    "Nome_Clima": "clima",
    "Nome_Outros_Manejos": "manejo",
    "UF": "uf",
    "Portaria": "portaria",
}

_REQUIRED_COLUMNS = {"Nome_cultura", "geocodigo", "dec1", "SafraIni", "SafraFin"}


def _build_safra(row: pd.Series) -> str:
    ini = str(row.get("SafraIni", "")).strip()
    fin = str(row.get("SafraFin", "")).strip()
    if not ini or fin.upper() == "PERENE":
        return "perene"
    return f"{ini}/{fin}"


def _normalize_cultura(x: object) -> str:
    if isinstance(x, str):
        return CULTURAS_ZARC.get(x.strip(), x.strip().lower().replace(" ", "_"))
    return ""


def parse_tabua_risco(csv_bytes: bytes) -> pd.DataFrame:
    if not csv_bytes:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    encoding = detect_encoding_chain(csv_bytes)
    text = csv_bytes.decode(encoding)

    df = pd.read_csv(
        StringIO(text),
        sep=";",
        dtype=str,
        low_memory=False,
        on_bad_lines="skip",
    )

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ParseError(
            source="zarc",
            parser_version=PARSER_VERSION,
            reason=f"Missing columns: {missing}",
        )

    df = df.rename(columns=_RENAME_MAP)

    df["safra"] = df.apply(_build_safra, axis=1)
    df["cultura"] = df["cultura_raw"].map(_normalize_cultura)

    dec_cols = [f"dec{i}" for i in range(1, 37)]
    for col in dec_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("solo_codigo", "ciclo_codigo"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_SAIDA].reset_index(drop=True)

    logger.info("zarc_parse_ok", records=len(df))
    return df
