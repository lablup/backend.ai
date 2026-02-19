from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

import ai.backend.common.metrics.multiprocess as mp_mod
from ai.backend.common.metrics.multiprocess import (
    cleanup_prometheus_multiprocess_dir,
    generate_latest_multiprocess,
    setup_prometheus_multiprocess_dir,
)


@pytest.fixture(autouse=True)
def _reset_multiprocess_state() -> Iterator[None]:
    """Reset the module-level global state before each test."""
    original_dir = mp_mod._multiprocess_dir
    original_env = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    yield
    mp_mod._multiprocess_dir = original_dir
    if original_env is not None:
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_env
    elif "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        del os.environ["PROMETHEUS_MULTIPROC_DIR"]


class TestSetupPrometheusMultiprocDir:
    def test_creates_directory_with_default_base(self, tmp_path: Path) -> None:
        with patch.object(mp_mod, "_DEFAULT_BASE_DIR", tmp_path):
            result = setup_prometheus_multiprocess_dir("manager")

        assert result == tmp_path / "manager"
        assert result.is_dir()
        assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == str(result)

    def test_cleans_stale_db_files(self, tmp_path: Path) -> None:
        prom_dir = tmp_path / "manager"
        prom_dir.mkdir(parents=True)
        (prom_dir / "gauge_liveall_123.db").touch()
        (prom_dir / "counter_456.db").touch()
        (prom_dir / "keep_this.txt").touch()

        with patch.object(mp_mod, "_DEFAULT_BASE_DIR", tmp_path):
            setup_prometheus_multiprocess_dir("manager")

        assert not (prom_dir / "gauge_liveall_123.db").exists()
        assert not (prom_dir / "counter_456.db").exists()
        assert (prom_dir / "keep_this.txt").exists()

    def test_idempotent_returns_same_path(self, tmp_path: Path) -> None:
        with patch.object(mp_mod, "_DEFAULT_BASE_DIR", tmp_path):
            first = setup_prometheus_multiprocess_dir("manager")
            second = setup_prometheus_multiprocess_dir("manager")

        assert first == second

    def test_idempotent_ignores_different_component(self, tmp_path: Path) -> None:
        """Once setup, calling again with different component still returns the first path."""
        with patch.object(mp_mod, "_DEFAULT_BASE_DIR", tmp_path):
            first = setup_prometheus_multiprocess_dir("manager")
            second = setup_prometheus_multiprocess_dir("agent")

        assert first == second  # idempotent, returns first result


class TestGenerateLatestMultiprocess:
    def test_returns_bytes_normally(self, tmp_path: Path) -> None:
        prom_dir = tmp_path / "test-component"
        prom_dir.mkdir(parents=True)
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(prom_dir)
        mp_mod._multiprocess_dir = prom_dir

        result = generate_latest_multiprocess()
        assert isinstance(result, bytes)

    def test_recovers_from_missing_directory(self, tmp_path: Path) -> None:
        prom_dir = tmp_path / "test-component"
        prom_dir.mkdir(parents=True)
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(prom_dir)
        mp_mod._multiprocess_dir = prom_dir

        # Simulate systemd-tmpfiles-clean deleting the directory
        prom_dir.rmdir()
        assert not prom_dir.exists()

        result = generate_latest_multiprocess()
        # Should recover by recreating the directory
        assert isinstance(result, bytes)
        assert prom_dir.exists()

    def test_returns_empty_bytes_on_unrecoverable_failure(self) -> None:
        # Set an invalid path that can't be recreated
        mp_mod._multiprocess_dir = Path("/nonexistent/impossible/path")
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/nonexistent/impossible/path"

        result = generate_latest_multiprocess()
        assert result == b""


class TestCleanupPrometheusMultiprocDir:
    def test_removes_directory_and_env(self, tmp_path: Path) -> None:
        prom_dir = tmp_path / "manager"
        prom_dir.mkdir(parents=True)
        (prom_dir / "test.db").touch()
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(prom_dir)
        mp_mod._multiprocess_dir = prom_dir

        cleanup_prometheus_multiprocess_dir()

        assert not prom_dir.exists()
        assert "PROMETHEUS_MULTIPROC_DIR" not in os.environ
        assert mp_mod._multiprocess_dir is None

    def test_noop_when_not_initialized(self) -> None:
        mp_mod._multiprocess_dir = None
        if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
            del os.environ["PROMETHEUS_MULTIPROC_DIR"]

        # Should not raise
        cleanup_prometheus_multiprocess_dir()
