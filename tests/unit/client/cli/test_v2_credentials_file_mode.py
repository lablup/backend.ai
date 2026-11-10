from __future__ import annotations

import stat
import tomllib
from pathlib import Path

import pytest

from ai.backend.client.cli.v2.config_cmd import _save_credentials_toml

_CREDENTIALS = {"backend-ai": {"access_key": "access", "secret_key": "secret"}}


@pytest.fixture
def credentials_path_before_first_save(tmp_path: Path, world_readable_umask: None) -> Path:
    return tmp_path / ".backend.ai" / "credentials.toml"


@pytest.fixture
def loose_credentials_path(credentials_path_before_first_save: Path) -> Path:
    credentials_path_before_first_save.parent.mkdir()
    credentials_path_before_first_save.write_text('[backend-ai]\naccess_key = "old"\n')
    credentials_path_before_first_save.chmod(0o644)
    return credentials_path_before_first_save


class TestSaveCredentialsToml:
    def test_new_file_is_owner_only(self, credentials_path_before_first_save: Path) -> None:
        _save_credentials_toml(credentials_path_before_first_save, _CREDENTIALS)

        assert stat.S_IMODE(credentials_path_before_first_save.stat().st_mode) == 0o600

    def test_loose_file_is_tightened_and_rewritten(self, loose_credentials_path: Path) -> None:
        _save_credentials_toml(loose_credentials_path, _CREDENTIALS)

        assert stat.S_IMODE(loose_credentials_path.stat().st_mode) == 0o600
        assert tomllib.loads(loose_credentials_path.read_text()) == _CREDENTIALS
