from __future__ import annotations

import asyncio
import hashlib
import json
import os
import ssl
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import structlog

from agrobr.constants import MIN_ZIP_SIZE, CacheSettings
from agrobr.exceptions import SourceUnavailableError
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator
from agrobr.utils.warnings import warn_once

from .models import BASE_URL, FILENAME_PATTERNS

logger = structlog.get_logger()

_CHUNK_SIZE = 64 * 1024

TIMEOUT = get_timeout(read=120.0)

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_FETCH_LOCKS: dict[str, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()


def _cache_disabled() -> bool:
    return os.environ.get("AGROBR_ACERVO_FUNDIARIO_CACHE_DISABLED") == "1"


async def _get_lock(key: str) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        lock = _FETCH_LOCKS.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _FETCH_LOCKS[key] = lock
        return lock


def _build_filename(tema: str, uf: str | None) -> str:
    pattern = FILENAME_PATTERNS[tema]
    return pattern.format(uf=uf) if uf else pattern


def _build_url(tema: str, uf: str | None) -> str:
    return BASE_URL + quote(_build_filename(tema, uf))


def _cache_key(tema: str, uf: str | None) -> str:
    return f"{tema}:{uf}" if uf else tema


def _cache_dir(tema: str) -> Path:
    settings = CacheSettings()
    return settings.cache_dir / "acervo_fundiario" / tema


def _zip_path(tema: str, uf: str | None) -> Path:
    name = uf if uf else "brasil"
    return _cache_dir(tema) / f"{name}.zip"


def _meta_path(tema: str, uf: str | None) -> Path:
    name = uf if uf else "brasil"
    return _cache_dir(tema) / f"{name}.json"


def _atomic_write_text(target: Path, text: str) -> None:
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def _cleanup_tmp_files(cdir: Path) -> None:
    if not cdir.exists():
        return
    for tmp in cdir.glob("*.tmp"):
        try:
            tmp.unlink()
        except OSError as exc:
            logger.debug("acervo_fundiario_cache_tmp_cleanup_failed", path=str(tmp), error=str(exc))


def _load_meta(meta_path: Path) -> dict[str, Any] | None:
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("acervo_fundiario_cache_meta_invalid", path=str(meta_path), error=str(exc))
        return None


def _save_meta(meta_path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(meta_path, json.dumps(payload, ensure_ascii=False, indent=2))


def _validate_zip_bytes_prefix(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(4)
    except OSError:
        return False
    return head == b"PK\x03\x04"


def _validate_cached_zip(zip_path: Path) -> bool:
    if not zip_path.exists():
        return False
    if zip_path.stat().st_size < MIN_ZIP_SIZE:
        logger.warning("acervo_fundiario_cache_zip_too_small", path=str(zip_path))
        return False
    if not _validate_zip_bytes_prefix(zip_path):
        logger.warning("acervo_fundiario_cache_zip_invalid_magic", path=str(zip_path))
        return False
    return True


async def _head(client: httpx.AsyncClient, url: str) -> dict[str, str | int]:
    response = await client.head(url, timeout=TIMEOUT)
    if response.status_code == 404:
        raise SourceUnavailableError(
            source="acervo_fundiario",
            url=url,
            last_error="HTTP 404 — recurso nao disponivel no servidor INCRA",
        )
    response.raise_for_status()
    headers = response.headers
    last_modified = headers.get("Last-Modified", "")
    etag = headers.get("ETag", "")
    content_length = int(headers.get("Content-Length", "0"))
    return {"last_modified": last_modified, "etag": etag, "content_length": content_length}


async def _stream_download(client: httpx.AsyncClient, url: str, dst_path: Path) -> tuple[int, str]:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_tmp_files(dst_path.parent)

    tmp = dst_path.with_suffix(dst_path.suffix + ".tmp")
    sha = hashlib.sha256()
    bytes_written = 0

    try:
        async with client.stream("GET", url, timeout=TIMEOUT) as response:
            if response.status_code == 404:
                raise SourceUnavailableError(
                    source="acervo_fundiario", url=url, last_error="HTTP 404"
                )
            response.raise_for_status()
            with open(tmp, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)
                    sha.update(chunk)
                    bytes_written += len(chunk)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    if bytes_written < MIN_ZIP_SIZE:
        tmp.unlink(missing_ok=True)
        raise SourceUnavailableError(
            source="acervo_fundiario",
            url=url,
            last_error=f"Resposta muito pequena ({bytes_written} bytes), esperado ZIP >={MIN_ZIP_SIZE}",
        )
    if not _validate_zip_bytes_prefix(tmp):
        tmp.unlink(missing_ok=True)
        raise SourceUnavailableError(
            source="acervo_fundiario",
            url=url,
            last_error="Resposta nao e um ZIP valido (magic bytes incorretas)",
        )

    os.replace(tmp, dst_path)
    return bytes_written, sha.hexdigest()


def _warn_download_size_once() -> None:
    warn_once(
        "acervo_fundiario_download_size",
        (
            "acervo_fundiario: download de shapefile estatico do INCRA. "
            "Tamanhos: SIGEF 8-687 MB por UF, SNCI 0.6-22 MB por UF, Assentamentos 48 MB. "
            "Cache em ~/.agrobr/cache/acervo_fundiario/ (opt-out: use_cache=False ou "
            "AGROBR_ACERVO_FUNDIARIO_CACHE_DISABLED=1)."
        ),
    )


async def download_and_cache(tema: str, uf: str | None = None, *, use_cache: bool = True) -> Path:
    if tema not in FILENAME_PATTERNS:
        raise ValueError(f"tema invalido: {tema!r}. Validos: {sorted(FILENAME_PATTERNS)}")

    url = _build_url(tema, uf)
    zip_path = _zip_path(tema, uf)
    meta_path = _meta_path(tema, uf)
    cache_active = use_cache and not _cache_disabled()

    lock = await _get_lock(_cache_key(tema, uf))
    async with (
        lock,
        httpx.AsyncClient(
            verify=_SSL_CTX,
            headers=UserAgentRotator.get_bot_headers(),
            follow_redirects=True,
        ) as client,
    ):
        head_info: dict[str, str | int] | None = None

        if cache_active:
            cached_meta = _load_meta(meta_path)
            if cached_meta and _validate_cached_zip(zip_path):
                head_info = await _head(client, url)
                if head_info["last_modified"] == cached_meta.get("last_modified"):
                    logger.debug(
                        "acervo_fundiario_cache_hit",
                        tema=tema,
                        uf=uf,
                        last_modified=head_info["last_modified"],
                    )
                    return zip_path
                logger.info(
                    "acervo_fundiario_cache_stale",
                    tema=tema,
                    uf=uf,
                    cached=cached_meta.get("last_modified"),
                    remote=head_info["last_modified"],
                )

        _warn_download_size_once()
        logger.info("acervo_fundiario_download_start", tema=tema, uf=uf, url=url)
        size_bytes, sha256 = await _stream_download(client, url, zip_path)

        if head_info is None:
            head_info = await _head(client, url)

        _save_meta(
            meta_path,
            {
                "tema": tema,
                "uf": uf,
                "source_url": url,
                "last_modified": head_info["last_modified"],
                "etag": head_info["etag"],
                "size_bytes": size_bytes,
                "sha256": sha256,
                "fetched_at": datetime.now(UTC).isoformat(),
            },
        )
        logger.info(
            "acervo_fundiario_download_ok",
            tema=tema,
            uf=uf,
            size_bytes=size_bytes,
            sha256=sha256[:16],
        )
        return zip_path
