from __future__ import annotations

import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.client.cli.v2 import v2


@pytest.fixture
def home_holding_loose_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    world_readable_umask: None,
) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("BACKEND_PROFILE", raising=False)
    credentials_path = tmp_path / ".backend.ai" / "credentials.toml"
    credentials_path.parent.mkdir()
    credentials_path.write_text('[backend-ai]\naccess_key = "old"\n')
    credentials_path.chmod(0o644)
    return tmp_path


class TestConfigSetCredentialsFileMode:
    def test_loose_credentials_file_is_tightened(
        self,
        runner: CliRunner,
        home_holding_loose_credentials: Path,
    ) -> None:
        result = runner.invoke(v2, ["config", "set", "secret-key", "secret"])

        assert result.exit_code == 0, result.output
        credentials_path = home_holding_loose_credentials / ".backend.ai" / "credentials.toml"
        assert stat.S_IMODE(credentials_path.stat().st_mode) == 0o600
