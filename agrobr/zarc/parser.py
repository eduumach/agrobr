from __future__ import annotations

from io import StringIO

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.normalize.encoding import detect_encoding_chain

from .models import COLUNAS_SAIDA, CULTURAS_ZARC, DEC_COLS

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

_USECOLS = (
    {"Nome_cultura", "SafraIni", "SafraFin", "geocodigo", "municipio"}
    | set(_RENAME_MAP.keys())
    | set(DEC_COLS)
)


def _normalize_cultura(x: object) -> str:
    if isinstance(x, str):
        return CULTURAS_ZARC.get(x.strip(), x.strip().lower().replace(" ", "_"))
    return ""


def parse_tabua_risco(csv_bytes: bytes) -> pd.DataFrame:
    if not csv_bytes:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    encoding = detect_encoding_chain(csv_bytes)
    text = csv_bytes.decode(encoding)

    sio = StringIO(text)
    df_probe = pd.read_csv(sio, sep=";", nrows=0)
    available = set(df_probe.columns)

    missing = _REQUIRED_COLUMNS - available
    if missing:
        raise ParseError(
            source="zarc",
            parser_version=PARSER_VERSION,
            reason=f"Missing columns: {missing}",
        )

    usecols = sorted(_USECOLS & available)
    sio.seek(0)
    df = pd.read_csv(
        sio,
        sep=";",
        dtype=str,
        usecols=usecols,
        low_memory=False,
        on_bad_lines="skip",
    )

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    df = df.rename(columns=_RENAME_MAP)

    safra_ini = df["SafraIni"].fillna("").astype(str).str.strip()
    safra_fin = df["SafraFin"].fillna("").astype(str).str.strip()
    is_perene = (safra_ini == "") | (safra_fin.str.upper() == "PERENE")
    df["safra"] = safra_ini + "/" + safra_fin
    df.loc[is_perene, "safra"] = "perene"

    df["cultura"] = df["cultura_raw"].map(_normalize_cultura)

    numeric_cols = [c for c in DEC_COLS if c in df.columns] + [
        c for c in ("solo_codigo", "ciclo_codigo") if c in df.columns
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)

    for col in COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_SAIDA].reset_index(drop=True)

    logger.info("zarc_parse_ok", records=len(df))
    return df
