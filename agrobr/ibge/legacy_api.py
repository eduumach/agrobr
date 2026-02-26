from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

import pandas as pd
import structlog

from agrobr.ibge import ftp_client, legacy_parser

if TYPE_CHECKING:
    from agrobr.models import MetaInfo

logger = structlog.get_logger()

TEMAS_LEGADO: list[str] = legacy_parser.TEMAS_LEGADO

_NIVEL_MAP: dict[str, str] = {
    "brasil": "totais",
    "uf": "mesorregiao",
    "municipio": "municipio",
}


async def censo_agro_legado(
    tema: str,
    uf: str | None = None,
    nivel: Literal["brasil", "uf", "municipio"] = "uf",
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    if tema not in TEMAS_LEGADO:
        raise ValueError(f"Tema '{tema}' não suportado. Disponíveis: {TEMAS_LEGADO}")

    t0 = time.monotonic()

    tab_name = ftp_client.LEGACY_TEMAS[tema]
    uf_dir = "Brasil"
    if uf:
        uf_upper = uf.upper()
        if uf_upper not in ftp_client.UF_DIRS:
            raise ValueError(f"UF '{uf}' inválida. Disponíveis: {sorted(ftp_client.UF_DIRS)}")
        uf_dir = ftp_client.UF_DIRS[uf_upper]

    zip_bytes = await ftp_client.download_legacy_zip(tab_name, uf_dir=uf_dir)
    xls_files = ftp_client.extract_xls_from_zip(zip_bytes)

    frames: list[pd.DataFrame] = []
    for filename, xls_data in xls_files:
        parsed = legacy_parser.parse_legacy_xls(xls_data, tema=tema, filename=filename)
        if not parsed.empty:
            frames.append(parsed)

    if not frames:
        df = pd.DataFrame(columns=legacy_parser._OUTPUT_COLS)
    else:
        df = pd.concat(frames, ignore_index=True)

    nivel_geo_value = _NIVEL_MAP.get(nivel)
    if nivel_geo_value and "nivel_geo" in df.columns:
        df = df[df["nivel_geo"] == nivel_geo_value].reset_index(drop=True)

    if "nivel_geo" in df.columns:
        df = df.drop(columns=["nivel_geo"])

    if not df.empty:
        sort_cols = [c for c in ["localidade", "categoria"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)

    elapsed = time.monotonic() - t0

    logger.info(
        "censo_agro_legado_ok",
        tema=tema,
        uf=uf,
        nivel=nivel,
        records=len(df),
        elapsed_s=round(elapsed, 2),
    )

    if as_polars:
        try:
            import polars as pl

            df = pl.from_pandas(df)
        except ImportError:
            pass

    if return_meta:
        from agrobr.models import MetaInfo

        now = datetime.now(UTC)
        meta = MetaInfo(
            source="ibge_censo_agro_legado",
            source_url=f"{ftp_client.FTP_BASE}/{uf_dir}/{tab_name}.zip",
            source_method="ftp_download",
            fetched_at=now,
            records_count=len(df) if not isinstance(df, tuple) else len(df),
            columns=list(df.columns) if hasattr(df, "columns") else [],
            from_cache=False,
            parser_version=legacy_parser.PARSER_VERSION,
            dataset="censo_agropecuario_legado",
            contract_version="1.0",
            snapshot=None,
            attempted_sources=["ibge_censo_agro_legado"],
            selected_source="ibge_censo_agro_legado",
            fetch_timestamp=now,
        )
        return df, meta

    return df


async def temas_censo_agro_legado() -> list[str]:
    return list(TEMAS_LEGADO)
