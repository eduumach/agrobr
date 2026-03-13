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
    d = CacheSettings().cache_dir / "defensivos"
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
        logger.info("defensivos_cache_stale", name=name)
        path.unlink(missing_ok=True)
        return None
    try:
        df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
        df = df.replace("", pd.NA)
    except Exception:
        logger.warning("defensivos_cache_corrupt", name=name)
        path.unlink(missing_ok=True)
        return None
    logger.info("defensivos_cache_hit", name=name, rows=len(df))
    return df


def write_cache(name: str, df: pd.DataFrame) -> None:
    path = _cache_dir() / f"{name}{_EXT}"
    df.to_csv(path, sep=";", index=False)
    logger.info("defensivos_cache_write", name=name, rows=len(df))


def write_formulados_pair(form_df: pd.DataFrame, auth_df: pd.DataFrame) -> None:
    write_cache("formulados", form_df)
    write_cache("autorizacoes", auth_df)


def invalidate() -> None:
    d = _cache_dir()
    for f in d.glob(f"*{_EXT}"):
        f.unlink()
    logger.info("defensivos_cache_invalidated")
