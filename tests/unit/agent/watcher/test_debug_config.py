from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ai.backend.agent.watcher import main

_ETCD_PASSWORD = "etcd-password-value"
_REDIS_SECRET = "redis-secret-value"


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "agent.toml"
    path.write_text(
        f"""
[etcd]
namespace = "visible-namespace"
user = "visible-user"
password = "{_ETCD_PASSWORD}"

[watcher]

[logging]

[extra.nested]
client-secret = "{_REDIS_SECRET}"
"""
    )
    return path


class TestDebugConfigOutput:
    @pytest.fixture
    def output(self, config_path: Path) -> str:
        with (
            patch("ai.backend.agent.watcher.aiotools.start_server"),
            patch("ai.backend.agent.watcher.Logger"),
            patch("ai.backend.agent.watcher.setproctitle"),
        ):
            result = CliRunner().invoke(main, ["--config", str(config_path), "--debug"])
        assert result.exit_code == 0, result.output
        return result.output

    def test_prints_configuration_without_secret_values(self, output: str) -> None:
        assert _ETCD_PASSWORD not in output
        assert _REDIS_SECRET not in output

    def test_prints_other_values(self, output: str) -> None:
        assert "== Watcher configuration ==" in output
        assert "visible-namespace" in output
        assert "visible-user" in output
