from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor

_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "token",
        "password",
        "secret",
        "credential",
        "ocp-apim-subscription-key",
    }
)

_SENSITIVE_QUERY_RE = re.compile(
    r"([?&])(api_key|apikey|token|key|password|secret)=[^&]*",
    re.IGNORECASE,
)


def _scrub_sensitive(
    _logger: Any,
    _method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    for key in event_dict:
        if key.lower().replace("-", "_") in _SENSITIVE_KEYS:
            event_dict[key] = "***"
        elif isinstance(event_dict[key], str):
            event_dict[key] = _SENSITIVE_QUERY_RE.sub(r"\1\2=***", event_dict[key])
    return event_dict


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Path | str | None = None,
) -> None:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _scrub_sensitive,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


configure_logging(level="INFO", json_format=True)
