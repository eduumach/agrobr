"""Utilitários gerais."""

from __future__ import annotations

from agrobr.utils.result import build_source_meta, finalize_result
from agrobr.utils.time import utcnow
from agrobr.utils.warnings import warn_once, warn_once_reset

__all__: list[str] = [
    "build_source_meta",
    "finalize_result",
    "utcnow",
    "warn_once",
    "warn_once_reset",
]
