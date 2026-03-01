from __future__ import annotations

import warnings

_warned_keys: set[str] = set()


def warn_once(
    key: str,
    message: str,
    category: type[Warning] = UserWarning,
    stacklevel: int = 2,
) -> None:
    if key not in _warned_keys:
        _warned_keys.add(key)
        warnings.warn(message, category, stacklevel=stacklevel + 1)


def warn_once_reset(key: str | None = None) -> None:
    if key is None:
        _warned_keys.clear()
    else:
        _warned_keys.discard(key)
