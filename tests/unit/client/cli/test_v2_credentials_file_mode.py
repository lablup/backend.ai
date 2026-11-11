from __future__ import annotations

import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.client.cli.v2 import config_cmd, v2


@pytest.fixture
def credentials_file_without_backend_ai_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    world_readable_umask: None,
) -> Path:
    credentials_path = tmp_path / ".backend.ai" / "credentials.toml"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_cmd, "CREDENTIALS_FILE", credentials_path)
    return credentials_path


class TestConfigSetCredentialsFileMode:
    def test_new_credentials_file_is_owner_only(
        self,
        runner: CliRunner,
        credentials_file_without_backend_ai_dir: Path,
    ) -> None:
        result = runner.invoke(v2, ["config", "set", "secret-key", "secret"])

        assert result.exit_code == 0, result.output
        assert stat.S_IMODE(credentials_file_without_backend_ai_dir.stat().st_mode) == 0o600
