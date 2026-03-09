"""Tests for snapshots module."""

from __future__ import annotations

import json
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from agrobr.snapshots import (
    SnapshotManifest,
    _validate_path_component,
    create_snapshot,
    delete_snapshot,
    get_snapshot,
    get_snapshots_dir,
    list_snapshots,
    load_from_snapshot,
)

try:
    import pyarrow  # noqa: F401

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

requires_pyarrow = pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")


def _make_manifest(
    name: str = "test",
    sources: list[str] | None = None,
) -> SnapshotManifest:
    return SnapshotManifest(
        name=name,
        created_at=datetime(2025, 1, 15, 10, 0),
        agrobr_version="0.3.0",
        sources=sources or [],
    )


def _write_manifest(path, manifest: SnapshotManifest) -> None:
    with open(path / "manifest.json", "w") as f:
        json.dump(manifest.to_dict(), f)


class TestSnapshotManifest:
    def test_manifest_creation(self):
        manifest = SnapshotManifest(
            name="2025-01-15",
            created_at=datetime(2025, 1, 15, 10, 30),
            agrobr_version="0.3.0",
            sources=["cepea", "conab"],
        )
        assert manifest.name == "2025-01-15"
        assert manifest.agrobr_version == "0.3.0"
        assert "cepea" in manifest.sources

    def test_manifest_to_dict(self):
        manifest = SnapshotManifest(
            name="test",
            created_at=datetime(2025, 1, 15, 10, 30),
            agrobr_version="0.3.0",
        )
        d = manifest.to_dict()
        assert d["name"] == "test"
        assert d["created_at"] == "2025-01-15T10:30:00"
        assert d["agrobr_version"] == "0.3.0"

    def test_manifest_from_dict(self):
        data = {
            "name": "2025-01-15",
            "created_at": "2025-01-15T10:30:00",
            "agrobr_version": "0.3.0",
            "sources": ["cepea"],
            "files": {},
            "metadata": {},
        }
        manifest = SnapshotManifest.from_dict(data)
        assert manifest.name == "2025-01-15"
        assert manifest.created_at == datetime(2025, 1, 15, 10, 30)

    def test_manifest_from_dict_datetime_already_parsed(self):
        dt = datetime(2025, 6, 1, 12, 0)
        data = {
            "name": "test",
            "created_at": dt,
            "agrobr_version": "0.3.0",
            "sources": [],
            "files": {},
            "metadata": {},
        }
        manifest = SnapshotManifest.from_dict(data)
        assert manifest.created_at is dt

    def test_manifest_roundtrip(self):
        original = SnapshotManifest(
            name="test",
            created_at=datetime(2025, 6, 15, 14, 0),
            agrobr_version="0.3.0",
            sources=["cepea", "ibge"],
            files={"cepea/soja.parquet": {"rows": 100}},
        )
        d = original.to_dict()
        restored = SnapshotManifest.from_dict(d)
        assert restored.name == original.name
        assert restored.sources == original.sources
        assert restored.files == original.files

    def test_manifest_to_dict_includes_all_fields(self):
        manifest = SnapshotManifest(
            name="full",
            created_at=datetime(2025, 3, 1),
            agrobr_version="0.5.0",
            sources=["cepea"],
            files={"cepea/soja.parquet": {"rows": 10}},
            metadata={"note": "test"},
        )
        d = manifest.to_dict()
        assert d["sources"] == ["cepea"]
        assert d["files"] == {"cepea/soja.parquet": {"rows": 10}}
        assert d["metadata"] == {"note": "test"}


class TestGetSnapshotsDir:
    def test_returns_config_snapshot_dir(self, tmp_path):
        mock_config = MagicMock()
        mock_config.get_snapshot_dir.return_value = tmp_path / "snaps"
        with patch("agrobr.snapshots.get_config", return_value=mock_config):
            result = get_snapshots_dir()
            assert result == tmp_path / "snaps"
            mock_config.get_snapshot_dir.assert_called_once()


class TestSnapshotOperations:
    def test_list_snapshots_empty(self, tmp_path):
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert snapshots == []

    def test_list_snapshots_nonexistent_dir(self, tmp_path):
        missing_dir = tmp_path / "does_not_exist"
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=missing_dir):
            snapshots = list_snapshots()
            assert snapshots == []

    def test_list_snapshots_with_data(self, tmp_path):
        snapshot_dir = tmp_path / "2025-01-15"
        snapshot_dir.mkdir()

        manifest = _make_manifest("2025-01-15", sources=["cepea"])
        _write_manifest(snapshot_dir, manifest)

        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert len(snapshots) == 1
            assert snapshots[0].name == "2025-01-15"

    def test_list_snapshots_skips_files(self, tmp_path):
        (tmp_path / "not_a_dir.txt").write_text("hello")
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert snapshots == []

    def test_list_snapshots_skips_dirs_without_manifest(self, tmp_path):
        (tmp_path / "no-manifest").mkdir()
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert snapshots == []

    def test_list_snapshots_counts_parquet_files(self, tmp_path):
        snapshot_dir = tmp_path / "snap1"
        snapshot_dir.mkdir()
        _write_manifest(snapshot_dir, _make_manifest("snap1", sources=["cepea"]))

        cepea_dir = snapshot_dir / "cepea"
        cepea_dir.mkdir()
        (cepea_dir / "soja.parquet").write_bytes(b"fake")
        (cepea_dir / "milho.parquet").write_bytes(b"fake")
        (cepea_dir / "readme.txt").write_text("not parquet")

        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert len(snapshots) == 1
            assert snapshots[0].file_count == 2
            assert snapshots[0].size_bytes > 0

    def test_list_snapshots_corrupt_manifest(self, tmp_path):
        snapshot_dir = tmp_path / "corrupt"
        snapshot_dir.mkdir()
        (snapshot_dir / "manifest.json").write_text("{invalid json")

        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshots = list_snapshots()
            assert snapshots == []

    def test_get_snapshot_found(self, tmp_path):
        snapshot_dir = tmp_path / "test-snapshot"
        snapshot_dir.mkdir()
        _write_manifest(snapshot_dir, _make_manifest("test-snapshot"))

        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshot = get_snapshot("test-snapshot")
            assert snapshot is not None
            assert snapshot.name == "test-snapshot"

    def test_get_snapshot_not_found(self, tmp_path):
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            snapshot = get_snapshot("nonexistent")
            assert snapshot is None

    def test_delete_snapshot_success(self, tmp_path):
        snapshot_dir = tmp_path / "to-delete"
        snapshot_dir.mkdir()
        _write_manifest(snapshot_dir, _make_manifest("to-delete"))

        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            result = delete_snapshot("to-delete")
            assert result is True
            assert not snapshot_dir.exists()

    def test_delete_snapshot_not_found(self, tmp_path):
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            result = delete_snapshot("nonexistent")
            assert result is False


class TestLoadFromSnapshot:
    @requires_pyarrow
    def test_load_parquet_success(self, tmp_path):
        snapshot_dir = tmp_path / "2025-01-15" / "cepea"
        snapshot_dir.mkdir(parents=True)

        df = pd.DataFrame({"produto": ["soja", "milho"], "valor": [150.0, 80.0]})
        df.to_parquet(snapshot_dir / "soja.parquet", index=False)

        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.config.get_config") as mock_config,
        ):
            mock_config.return_value.snapshot_date = None
            loaded = load_from_snapshot("cepea", "soja", snapshot_name="2025-01-15")

            assert loaded is not None
            assert len(loaded) == 2
            assert "soja" in loaded["produto"].values

    def test_load_file_not_found(self, tmp_path):
        snapshot_dir = tmp_path / "2025-01-15" / "cepea"
        snapshot_dir.mkdir(parents=True)

        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.config.get_config") as mock_config,
        ):
            mock_config.return_value.snapshot_date = None
            loaded = load_from_snapshot("cepea", "trigo", snapshot_name="2025-01-15")
            assert loaded is None

    def test_load_no_snapshot_specified(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.config.get_config") as mock_config,
        ):
            mock_config.return_value.snapshot_date = None
            with pytest.raises(ValueError, match="No snapshot specified"):
                load_from_snapshot("cepea", "soja")

    @requires_pyarrow
    def test_load_uses_config_snapshot_date(self, tmp_path):
        snapshot_dir = tmp_path / "2025-06-01" / "conab"
        snapshot_dir.mkdir(parents=True)

        df = pd.DataFrame({"safra": ["2024/25"], "valor": [100.0]})
        df.to_parquet(snapshot_dir / "safras.parquet", index=False)

        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots.get_config") as mock_config,
        ):
            mock_config.return_value.snapshot_date = date(2025, 6, 1)
            loaded = load_from_snapshot("conab", "safras")
            assert loaded is not None
            assert len(loaded) == 1


class TestPathTraversalProtection:
    TRAVERSAL_PAYLOADS = [
        "../../etc/passwd",
        "..\\..\\windows",
        "../..",
        "foo/bar",
        "foo\\bar",
        "",
        ".hidden",
    ]

    def test_validate_path_component_rejects_traversal(self):
        for payload in self.TRAVERSAL_PAYLOADS:
            with pytest.raises(ValueError):
                _validate_path_component(payload, "name")

    def test_validate_path_component_accepts_valid(self):
        for name in ["2025-01-15", "my_snapshot", "v1.0.0", "test123"]:
            _validate_path_component(name, "name")

    def test_delete_snapshot_rejects_traversal(self, tmp_path):
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            for payload in self.TRAVERSAL_PAYLOADS:
                with pytest.raises(ValueError):
                    delete_snapshot(payload)

    def test_load_from_snapshot_rejects_traversal(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.config.get_config") as mock_config,
        ):
            mock_config.return_value.snapshot_date = None
            with pytest.raises(ValueError):
                load_from_snapshot("../../etc", "passwd", snapshot_name="2025-01-15")
            with pytest.raises(ValueError):
                load_from_snapshot("cepea", "../../etc", snapshot_name="2025-01-15")
            with pytest.raises(ValueError):
                load_from_snapshot("cepea", "soja", snapshot_name="../../etc")

    @pytest.mark.asyncio
    async def test_create_snapshot_rejects_traversal(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            pytest.raises(ValueError),
        ):
            await create_snapshot(name="../../etc")


class TestCreateSnapshot:
    @pytest.mark.asyncio
    async def test_create_snapshot_default_name(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock),
        ):
            result = await create_snapshot()
            assert result is not None
            assert result.name == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_create_snapshot_custom_name(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock),
        ):
            result = await create_snapshot(name="my-snap")
            assert result is not None
            assert result.name == "my-snap"

    @pytest.mark.asyncio
    async def test_create_snapshot_default_sources(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock) as mock_cepea,
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock) as mock_conab,
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock) as mock_ibge,
        ):
            result = await create_snapshot(name="test-defaults")
            assert result is not None
            mock_cepea.assert_awaited_once()
            mock_conab.assert_awaited_once()
            mock_ibge.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_custom_sources(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock) as mock_cepea,
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock) as mock_conab,
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock) as mock_ibge,
        ):
            result = await create_snapshot(name="only-cepea", sources=["cepea"])
            assert result is not None
            mock_cepea.assert_awaited_once()
            mock_conab.assert_not_awaited()
            mock_ibge.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_snapshot_already_exists(self, tmp_path):
        existing = tmp_path / "existing"
        existing.mkdir()

        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            pytest.raises(ValueError, match="already exists"),
        ):
            await create_snapshot(name="existing")

    @pytest.mark.asyncio
    async def test_create_snapshot_writes_manifest(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock),
        ):
            await create_snapshot(name="manifest-check")

        manifest_path = tmp_path / "manifest-check" / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            data = json.load(f)
        assert data["name"] == "manifest-check"
        assert data["sources"] == ["cepea", "conab", "ibge"]
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_snapshot_creates_source_dirs(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch("agrobr.snapshots._snapshot_cepea", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock),
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock),
        ):
            await create_snapshot(name="dirs-check", sources=["cepea", "conab"])

        assert (tmp_path / "dirs-check" / "cepea").is_dir()
        assert (tmp_path / "dirs-check" / "conab").is_dir()

    @pytest.mark.asyncio
    async def test_create_snapshot_source_error_continues(self, tmp_path):
        with (
            patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path),
            patch(
                "agrobr.snapshots._snapshot_cepea",
                new_callable=AsyncMock,
                side_effect=RuntimeError("cepea broke"),
            ),
            patch("agrobr.snapshots._snapshot_conab", new_callable=AsyncMock) as mock_conab,
            patch("agrobr.snapshots._snapshot_ibge", new_callable=AsyncMock) as mock_ibge,
        ):
            result = await create_snapshot(name="error-resilient")
            assert result is not None
            mock_conab.assert_awaited_once()
            mock_ibge.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_unknown_source_ignored(self, tmp_path):
        with patch("agrobr.snapshots.get_snapshots_dir", return_value=tmp_path):
            result = await create_snapshot(name="unknown-src", sources=["banana"])
            assert result is not None
            assert (tmp_path / "unknown-src" / "banana").is_dir()


class TestSnapshotCepea:
    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_cepea_success(self, tmp_path):
        from agrobr.snapshots import _snapshot_cepea

        manifest = _make_manifest("test")
        df = pd.DataFrame({"data": ["2025-01-01"], "valor": [150.0]})

        with (
            patch("agrobr.cepea.produtos", new_callable=AsyncMock, return_value=["soja"]),
            patch("agrobr.cepea.indicador", new_callable=AsyncMock, return_value=df),
        ):
            await _snapshot_cepea(tmp_path, manifest)

        assert (tmp_path / "soja.parquet").exists()
        assert "cepea/soja.parquet" in manifest.files
        assert manifest.files["cepea/soja.parquet"]["rows"] == 1

    @pytest.mark.asyncio
    async def test_snapshot_cepea_empty_df(self, tmp_path):
        from agrobr.snapshots import _snapshot_cepea

        manifest = _make_manifest("test")
        empty_df = pd.DataFrame()

        with (
            patch("agrobr.cepea.produtos", new_callable=AsyncMock, return_value=["soja"]),
            patch("agrobr.cepea.indicador", new_callable=AsyncMock, return_value=empty_df),
        ):
            await _snapshot_cepea(tmp_path, manifest)

        assert not (tmp_path / "soja.parquet").exists()
        assert "cepea/soja.parquet" not in manifest.files

    @pytest.mark.asyncio
    async def test_snapshot_cepea_none_df(self, tmp_path):
        from agrobr.snapshots import _snapshot_cepea

        manifest = _make_manifest("test")

        with (
            patch("agrobr.cepea.produtos", new_callable=AsyncMock, return_value=["soja"]),
            patch("agrobr.cepea.indicador", new_callable=AsyncMock, return_value=None),
        ):
            await _snapshot_cepea(tmp_path, manifest)

        assert not (tmp_path / "soja.parquet").exists()

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_cepea_produto_error(self, tmp_path):
        from agrobr.snapshots import _snapshot_cepea

        manifest = _make_manifest("test")
        df = pd.DataFrame({"data": ["2025-01-01"], "valor": [100.0]})

        with (
            patch(
                "agrobr.cepea.produtos",
                new_callable=AsyncMock,
                return_value=["soja", "milho"],
            ),
            patch(
                "agrobr.cepea.indicador",
                new_callable=AsyncMock,
                side_effect=[RuntimeError("fail"), df],
            ),
        ):
            await _snapshot_cepea(tmp_path, manifest)

        assert not (tmp_path / "soja.parquet").exists()
        assert (tmp_path / "milho.parquet").exists()
        assert "cepea/milho.parquet" in manifest.files

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_cepea_multiple_products(self, tmp_path):
        from agrobr.snapshots import _snapshot_cepea

        manifest = _make_manifest("test")
        df1 = pd.DataFrame({"data": ["2025-01-01"], "valor": [150.0]})
        df2 = pd.DataFrame({"data": ["2025-01-01"], "valor": [80.0]})

        with (
            patch(
                "agrobr.cepea.produtos",
                new_callable=AsyncMock,
                return_value=["soja", "milho"],
            ),
            patch(
                "agrobr.cepea.indicador",
                new_callable=AsyncMock,
                side_effect=[df1, df2],
            ),
        ):
            await _snapshot_cepea(tmp_path, manifest)

        assert (tmp_path / "soja.parquet").exists()
        assert (tmp_path / "milho.parquet").exists()
        assert len(manifest.files) == 2


class TestSnapshotConab:
    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_conab_success(self, tmp_path):
        from agrobr.snapshots import _snapshot_conab

        manifest = _make_manifest("test")
        df_safras = pd.DataFrame({"safra": ["2024/25"], "producao": [100.0]})
        df_balanco = pd.DataFrame({"item": ["oferta"], "valor": [200.0]})

        with (
            patch("agrobr.conab.safras", new_callable=AsyncMock, return_value=df_safras),
            patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=df_balanco),
        ):
            await _snapshot_conab(tmp_path, manifest)

        assert (tmp_path / "safras.parquet").exists()
        assert (tmp_path / "balanco.parquet").exists()
        assert manifest.files["conab/safras.parquet"]["rows"] == 1
        assert manifest.files["conab/balanco.parquet"]["rows"] == 1

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_conab_empty_safras(self, tmp_path):
        from agrobr.snapshots import _snapshot_conab

        manifest = _make_manifest("test")
        df_balanco = pd.DataFrame({"item": ["oferta"], "valor": [200.0]})

        with (
            patch("agrobr.conab.safras", new_callable=AsyncMock, return_value=pd.DataFrame()),
            patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=df_balanco),
        ):
            await _snapshot_conab(tmp_path, manifest)

        assert not (tmp_path / "safras.parquet").exists()
        assert (tmp_path / "balanco.parquet").exists()

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_conab_safras_error(self, tmp_path):
        from agrobr.snapshots import _snapshot_conab

        manifest = _make_manifest("test")
        df_balanco = pd.DataFrame({"item": ["oferta"], "valor": [200.0]})

        with (
            patch(
                "agrobr.conab.safras",
                new_callable=AsyncMock,
                side_effect=RuntimeError("fail"),
            ),
            patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=df_balanco),
        ):
            await _snapshot_conab(tmp_path, manifest)

        assert not (tmp_path / "safras.parquet").exists()
        assert (tmp_path / "balanco.parquet").exists()

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_conab_balanco_error(self, tmp_path):
        from agrobr.snapshots import _snapshot_conab

        manifest = _make_manifest("test")
        df_safras = pd.DataFrame({"safra": ["2024/25"], "producao": [100.0]})

        with (
            patch("agrobr.conab.safras", new_callable=AsyncMock, return_value=df_safras),
            patch(
                "agrobr.conab.balanco",
                new_callable=AsyncMock,
                side_effect=RuntimeError("fail"),
            ),
        ):
            await _snapshot_conab(tmp_path, manifest)

        assert (tmp_path / "safras.parquet").exists()
        assert not (tmp_path / "balanco.parquet").exists()

    @pytest.mark.asyncio
    async def test_snapshot_conab_none_results(self, tmp_path):
        from agrobr.snapshots import _snapshot_conab

        manifest = _make_manifest("test")

        with (
            patch("agrobr.conab.safras", new_callable=AsyncMock, return_value=None),
            patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=None),
        ):
            await _snapshot_conab(tmp_path, manifest)

        assert not (tmp_path / "safras.parquet").exists()
        assert not (tmp_path / "balanco.parquet").exists()
        assert len(manifest.files) == 0


class TestSnapshotIbge:
    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_ibge_success(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")
        df_pam = pd.DataFrame({"produto": ["soja"], "producao": [100.0]})
        df_lspa = pd.DataFrame({"produto": ["soja"], "previsao": [95.0]})

        with (
            patch("agrobr.ibge.pam", new_callable=AsyncMock, return_value=df_pam),
            patch("agrobr.ibge.lspa", new_callable=AsyncMock, return_value=df_lspa),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert (tmp_path / "pam.parquet").exists()
        assert (tmp_path / "lspa.parquet").exists()
        assert manifest.files["ibge/pam.parquet"]["rows"] == 1
        assert manifest.files["ibge/lspa.parquet"]["rows"] == 1

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_ibge_empty_pam(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")
        df_lspa = pd.DataFrame({"produto": ["soja"], "previsao": [95.0]})

        with (
            patch("agrobr.ibge.pam", new_callable=AsyncMock, return_value=pd.DataFrame()),
            patch("agrobr.ibge.lspa", new_callable=AsyncMock, return_value=df_lspa),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert not (tmp_path / "pam.parquet").exists()
        assert (tmp_path / "lspa.parquet").exists()

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_ibge_pam_error(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")
        df_lspa = pd.DataFrame({"produto": ["soja"], "previsao": [95.0]})

        with (
            patch(
                "agrobr.ibge.pam",
                new_callable=AsyncMock,
                side_effect=RuntimeError("fail"),
            ),
            patch("agrobr.ibge.lspa", new_callable=AsyncMock, return_value=df_lspa),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert not (tmp_path / "pam.parquet").exists()
        assert (tmp_path / "lspa.parquet").exists()

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_ibge_lspa_error(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")
        df_pam = pd.DataFrame({"produto": ["soja"], "producao": [100.0]})

        with (
            patch("agrobr.ibge.pam", new_callable=AsyncMock, return_value=df_pam),
            patch(
                "agrobr.ibge.lspa",
                new_callable=AsyncMock,
                side_effect=RuntimeError("fail"),
            ),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert (tmp_path / "pam.parquet").exists()
        assert not (tmp_path / "lspa.parquet").exists()

    @pytest.mark.asyncio
    async def test_snapshot_ibge_none_results(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")

        with (
            patch("agrobr.ibge.pam", new_callable=AsyncMock, return_value=None),
            patch("agrobr.ibge.lspa", new_callable=AsyncMock, return_value=None),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert not (tmp_path / "pam.parquet").exists()
        assert not (tmp_path / "lspa.parquet").exists()
        assert len(manifest.files) == 0

    @requires_pyarrow
    @pytest.mark.asyncio
    async def test_snapshot_ibge_records_columns(self, tmp_path):
        from agrobr.snapshots import _snapshot_ibge

        manifest = _make_manifest("test")
        df_pam = pd.DataFrame({"produto": ["soja"], "area": [1000], "producao": [3000]})

        with (
            patch("agrobr.ibge.pam", new_callable=AsyncMock, return_value=df_pam),
            patch("agrobr.ibge.lspa", new_callable=AsyncMock, return_value=pd.DataFrame()),
        ):
            await _snapshot_ibge(tmp_path, manifest)

        assert manifest.files["ibge/pam.parquet"]["columns"] == ["produto", "area", "producao"]
