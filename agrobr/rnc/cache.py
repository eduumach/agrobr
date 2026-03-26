from __future__ import annotations

from pathlib import Path

import pandas as pd
import structlog

from agrobr.constants import CacheSettings
from agrobr.utils.time import utcnow

logger = structlog.get_logger()

TTL_SECONDS = 86400

_EXT = ".csv"


def _cache_dir() -> Path:
    d = CacheSettings().cache_dir / "rnc"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    from datetime import UTC, datetime

    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(tzinfo=None)
    return (utcnow() - mtime).total_seconds() < TTL_SECONDS


def read_cached(name: str) -> pd.DataFrame | None:
    path = _cache_dir() / f"{name}{_EXT}"
    if not path.exists():
        return None
    if not _is_fresh(path):
        logger.info("rnc_cache_stale", name=name)
        path.unlink(missing_ok=True)
        return None
    try:
        df = pd.read_csv(path, sep=",", dtype=str, keep_default_na=False)
        from .models import DATE_COLS_PROT, DATE_COLS_REG

        date_cols = DATE_COLS_REG if name == "registradas" else DATE_COLS_PROT
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    except Exception:
        logger.warning("rnc_cache_corrupt", name=name)
        path.unlink(missing_ok=True)
        return None
    logger.info("rnc_cache_hit", name=name, rows=len(df))
    return df


def write_cache(name: str, df: pd.DataFrame) -> None:
    path = _cache_dir() / f"{name}{_EXT}"
    df.to_csv(path, sep=",", index=False)
    logger.info("rnc_cache_write", name=name, rows=len(df))
