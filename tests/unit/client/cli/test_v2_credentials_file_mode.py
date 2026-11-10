from __future__ import annotations

import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.client.cli.v2 import v2


@pytest.fixture
def home_without_backend_ai_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    world_readable_umask: None,
) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("BACKEND_PROFILE", raising=False)
    return tmp_path


class TestConfigSetCredentialsFileMode:
    def test_new_credentials_file_is_owner_only(
        self,
        runner: CliRunner,
        home_without_backend_ai_dir: Path,
    ) -> None:
        result = runner.invoke(v2, ["config", "set", "secret-key", "secret"])

        assert result.exit_code == 0, result.output
        credentials_path = home_without_backend_ai_dir / ".backend.ai" / "credentials.toml"
        assert stat.S_IMODE(credentials_path.stat().st_mode) == 0o600
