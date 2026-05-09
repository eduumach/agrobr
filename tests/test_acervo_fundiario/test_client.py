from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from agrobr.acervo_fundiario import client
from agrobr.exceptions import SourceUnavailableError


class TestCacheKeyHelpers:
    def test_cache_key_with_uf(self):
        assert client._cache_key("sigef", "GO") == "sigef:GO"

    def test_cache_key_without_uf(self):
        assert client._cache_key("assentamentos", None) == "assentamentos"

    def test_zip_path_with_uf(self, isolated_cache):  # noqa: ARG002
        path = client._zip_path("sigef", "GO")
        assert path.name == "GO.zip"
        assert "sigef" in str(path)

    def test_zip_path_without_uf(self, isolated_cache):  # noqa: ARG002
        path = client._zip_path("assentamentos", None)
        assert path.name == "brasil.zip"

    def test_meta_path_pairs_with_zip(self, isolated_cache):  # noqa: ARG002
        zp = client._zip_path("sigef", "GO")
        mp = client._meta_path("sigef", "GO")
        assert zp.parent == mp.parent
        assert mp.suffix == ".json"


class TestUrlBuilding:
    def test_url_sigef_uf_quoted(self):
        url = client._build_url("sigef", "GO")
        assert url.startswith("https://certificacao.incra.gov.br/csv_shp/zip/")
        assert "Sigef" in url
        assert "GO" in url

    def test_url_snci_special_char_encoded(self):
        url = client._build_url("snci", "GO")
        assert "%C3%B3" in url or "Im%C3%B3vel" in url

    def test_url_assentamentos_no_uf(self):
        url = client._build_url("assentamentos", None)
        assert "Assentamento" in url


class TestZipValidation:
    def test_valid_zip_magic_bytes(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        zip_path.write_bytes(b"PK\x03\x04" + b"\x00" * 1000)
        assert client._validate_zip_bytes_prefix(zip_path) is True

    def test_invalid_magic_bytes(self, tmp_path):
        zip_path = tmp_path / "fake.zip"
        zip_path.write_bytes(b"<html>not a zip</html>" + b"\x00" * 500)
        assert client._validate_zip_bytes_prefix(zip_path) is False

    def test_validate_cached_zip_too_small(self, tmp_path):
        zip_path = tmp_path / "tiny.zip"
        zip_path.write_bytes(b"PK")
        assert client._validate_cached_zip(zip_path) is False

    def test_validate_cached_zip_missing(self, tmp_path):
        zip_path = tmp_path / "missing.zip"
        assert client._validate_cached_zip(zip_path) is False

    def test_validate_cached_zip_ok(self, tmp_path):
        zip_path = tmp_path / "ok.zip"
        zip_path.write_bytes(b"PK\x03\x04" + b"\x00" * 1000)
        assert client._validate_cached_zip(zip_path) is True


class TestAtomicWrites:
    def test_atomic_write_text(self, tmp_path):
        target = tmp_path / "data.json"
        client._atomic_write_text(target, '{"k": "v"}')
        assert json.loads(target.read_text(encoding="utf-8")) == {"k": "v"}

    def test_cleanup_tmp_files(self, tmp_path):
        (tmp_path / "a.tmp").touch()
        (tmp_path / "b.tmp").touch()
        (tmp_path / "keep.txt").touch()
        client._cleanup_tmp_files(tmp_path)
        assert not (tmp_path / "a.tmp").exists()
        assert not (tmp_path / "b.tmp").exists()
        assert (tmp_path / "keep.txt").exists()

    def test_cleanup_tmp_nonexistent_dir(self, tmp_path):
        client._cleanup_tmp_files(tmp_path / "missing")


class TestMetaPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        meta_path = tmp_path / "meta.json"
        payload = {"last_modified": "abc", "etag": "xyz", "size_bytes": 1234}
        client._save_meta(meta_path, payload)
        loaded = client._load_meta(meta_path)
        assert loaded == payload

    def test_load_missing_returns_none(self, tmp_path):
        assert client._load_meta(tmp_path / "missing.json") is None

    def test_load_invalid_json_returns_none(self, tmp_path):
        meta_path = tmp_path / "broken.json"
        meta_path.write_text("not json", encoding="utf-8")
        assert client._load_meta(meta_path) is None


class TestCacheDisabled:
    def test_env_var_set(self, monkeypatch):
        monkeypatch.setenv("AGROBR_ACERVO_FUNDIARIO_CACHE_DISABLED", "1")
        assert client._cache_disabled() is True

    def test_env_var_unset(self, monkeypatch):
        monkeypatch.delenv("AGROBR_ACERVO_FUNDIARIO_CACHE_DISABLED", raising=False)
        assert client._cache_disabled() is False


@pytest.mark.asyncio
class TestLockManagement:
    async def test_get_lock_returns_same_for_same_key(self):
        l1 = await client._get_lock("sigef:GO")
        l2 = await client._get_lock("sigef:GO")
        assert l1 is l2

    async def test_get_lock_returns_different_for_different_keys(self):
        l1 = await client._get_lock("sigef:GO")
        l2 = await client._get_lock("sigef:MG")
        assert l1 is not l2


@pytest.mark.asyncio
@pytest.mark.usefixtures("isolated_cache")
class TestDownloadAndCache:
    async def test_invalid_tema_raises(self):
        with pytest.raises(ValueError, match="tema invalido"):
            await client.download_and_cache("invalid_tema", "GO")

    async def test_cache_miss_streams_and_saves(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        head_payload = {
            "last_modified": "Sat, 09 May 2026 12:00:00 GMT",
            "etag": '"abc123"',
            "content_length": len(synthetic_bytes),
        }

        async def fake_head(_client, _url):
            return head_payload

        async def fake_stream(_client, _url, dst_path: Path):
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_bytes(synthetic_bytes)
            import hashlib

            return len(synthetic_bytes), hashlib.sha256(synthetic_bytes).hexdigest()

        monkeypatch.setattr(client, "_head", fake_head)
        monkeypatch.setattr(client, "_stream_download", fake_stream)

        zip_path = await client.download_and_cache("sigef", "ES")

        assert zip_path.exists()
        assert zip_path.stat().st_size == len(synthetic_bytes)
        meta = client._load_meta(client._meta_path("sigef", "ES"))
        assert meta is not None
        assert meta["last_modified"] == head_payload["last_modified"]
        assert meta["sha256"]

    async def test_cache_hit_does_not_redownload(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        zip_path = client._zip_path("sigef", "ES")
        meta_path = client._meta_path("sigef", "ES")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(synthetic_bytes)
        client._save_meta(
            meta_path,
            {
                "last_modified": "Sat, 09 May 2026 12:00:00 GMT",
                "etag": '"abc"',
                "size_bytes": len(synthetic_bytes),
                "sha256": "fake",
                "fetched_at": "2026-05-09T12:00:00+00:00",
            },
        )

        async def fake_head(_client, _url):
            return {
                "last_modified": "Sat, 09 May 2026 12:00:00 GMT",
                "etag": '"abc"',
                "content_length": len(synthetic_bytes),
            }

        stream_mock = AsyncMock()
        monkeypatch.setattr(client, "_head", fake_head)
        monkeypatch.setattr(client, "_stream_download", stream_mock)

        result = await client.download_and_cache("sigef", "ES")
        assert result == zip_path
        stream_mock.assert_not_called()

    async def test_cache_stale_redownloads(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        zip_path = client._zip_path("sigef", "ES")
        meta_path = client._meta_path("sigef", "ES")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(synthetic_bytes)
        client._save_meta(
            meta_path,
            {
                "last_modified": "Fri, 08 May 2026 09:00:00 GMT",
                "etag": '"old"',
                "size_bytes": len(synthetic_bytes),
                "sha256": "old",
                "fetched_at": "2026-05-08T09:00:00+00:00",
            },
        )

        async def fake_head(_client, _url):
            return {
                "last_modified": "Sat, 09 May 2026 12:00:00 GMT",
                "etag": '"new"',
                "content_length": len(synthetic_bytes),
            }

        stream_called = False

        async def fake_stream(_client, _url, dst_path: Path):
            nonlocal stream_called
            stream_called = True
            dst_path.write_bytes(synthetic_bytes)
            return len(synthetic_bytes), "newsha"

        monkeypatch.setattr(client, "_head", fake_head)
        monkeypatch.setattr(client, "_stream_download", fake_stream)

        await client.download_and_cache("sigef", "ES")
        assert stream_called

    async def test_use_cache_false_bypasses(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        zip_path = client._zip_path("sigef", "ES")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(synthetic_bytes)
        client._save_meta(
            client._meta_path("sigef", "ES"),
            {"last_modified": "x", "etag": "y", "size_bytes": 100, "sha256": "z"},
        )

        stream_called = False

        async def fake_stream(_client, _url, dst_path: Path):
            nonlocal stream_called
            stream_called = True
            dst_path.write_bytes(synthetic_bytes)
            return len(synthetic_bytes), "sha"

        async def fake_head(_client, _url):
            return {"last_modified": "x", "etag": "y", "content_length": 100}

        monkeypatch.setattr(client, "_stream_download", fake_stream)
        monkeypatch.setattr(client, "_head", fake_head)

        await client.download_and_cache("sigef", "ES", use_cache=False)
        assert stream_called

    async def test_env_disable_bypasses(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        zip_path = client._zip_path("sigef", "ES")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(synthetic_bytes)
        client._save_meta(
            client._meta_path("sigef", "ES"),
            {"last_modified": "x", "size_bytes": 100, "sha256": "z"},
        )

        monkeypatch.setenv("AGROBR_ACERVO_FUNDIARIO_CACHE_DISABLED", "1")

        stream_called = False

        async def fake_stream(_client, _url, dst_path: Path):
            nonlocal stream_called
            stream_called = True
            dst_path.write_bytes(synthetic_bytes)
            return len(synthetic_bytes), "sha"

        async def fake_head(_client, _url):
            return {"last_modified": "x", "etag": "y", "content_length": 100}

        monkeypatch.setattr(client, "_stream_download", fake_stream)
        monkeypatch.setattr(client, "_head", fake_head)

        await client.download_and_cache("sigef", "ES")
        assert stream_called

    async def test_concurrent_same_uf_serializes(self, monkeypatch, synthetic_sigef_zip: Path):
        synthetic_bytes = synthetic_sigef_zip.read_bytes()
        download_count = 0

        async def fake_stream(_client, _url, dst_path: Path):
            nonlocal download_count
            await asyncio.sleep(0.05)
            download_count += 1
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_bytes(synthetic_bytes)
            return len(synthetic_bytes), "sha"

        async def fake_head(_client, _url):
            return {
                "last_modified": "Sat, 09 May 2026 12:00:00 GMT",
                "etag": '"x"',
                "content_length": len(synthetic_bytes),
            }

        monkeypatch.setattr(client, "_stream_download", fake_stream)
        monkeypatch.setattr(client, "_head", fake_head)

        results = await asyncio.gather(
            client.download_and_cache("sigef", "ES"),
            client.download_and_cache("sigef", "ES"),
        )
        assert results[0] == results[1]
        assert download_count == 1


@pytest.mark.asyncio
async def test_head_404_raises_source_unavailable():
    class FakeResp:
        status_code = 404
        headers: dict[str, str] = {}

        def raise_for_status(self):
            pass

    class FakeClient:
        async def head(self, _url, timeout=None):  # noqa: ARG002
            return FakeResp()

    with pytest.raises(SourceUnavailableError, match="HTTP 404"):
        await client._head(FakeClient(), "https://example.com/missing.zip")  # type: ignore[arg-type]
