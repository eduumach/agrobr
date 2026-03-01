"""Utilitários gerais."""

from __future__ import annotations

from agrobr.utils.result import finalize_result
from agrobr.utils.time import utcnow
from agrobr.utils.warnings import warn_once, warn_once_reset

__all__: list[str] = ["finalize_result", "utcnow", "warn_once", "warn_once_reset"]
