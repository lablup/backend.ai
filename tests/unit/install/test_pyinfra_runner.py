"""Tests for pyinfra subprocess runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.install.pyinfra_runner import (
    _find_deploy_script,
    _find_run_local,
)


class TestFindRunLocal:
    def test_returns_path(self) -> None:
        path = _find_run_local()
        assert isinstance(path, Path)
        assert path.name == "run_local.py"

    def test_path_exists(self) -> None:
        path = _find_run_local()
        assert path.exists()


class TestFindDeployScript:
    @pytest.mark.parametrize(
        "service",
        [
            "manager",
            "agent",
            "storage_proxy",
            "webserver",
            "appproxy_coordinator",
            "appproxy_worker_interactive",
            "appproxy_worker_tcp",
        ],
    )
    def test_known_services(self, service: str) -> None:
        path = _find_deploy_script(service)
        assert path.exists()
        assert path.name == "deploy.py"

    def test_unknown_service(self) -> None:
        with pytest.raises(FileNotFoundError):
            _find_deploy_script("nonexistent")
