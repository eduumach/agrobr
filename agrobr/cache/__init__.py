"""Cache DuckDB com separação cache/histórico."""

from __future__ import annotations

from .duckdb_store import DuckDBStore, get_store
from .keys import build_cache_key
from .policies import (
    TTL,
    CachePolicy,
    calculate_expiry,
    get_policy,
)

__all__ = [
    "DuckDBStore",
    "get_store",
    "CachePolicy",
    "TTL",
    "get_policy",
    "calculate_expiry",
    "build_cache_key",
]
