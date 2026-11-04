from __future__ import annotations

import stat
from collections.abc import Callable
from pathlib import Path

import click
import pytest
from click.testing import CliRunner


@pytest.fixture
def loose_credentials_file(isolated_home: Path) -> Path:
    credentials_file = isolated_home / ".backend.ai" / "credentials.toml"
    credentials_file.parent.mkdir()
    credentials_file.write_text('[backend-ai]\naccess_key = "existing-access-key"\n')
    credentials_file.chmod(0o644)
    return credentials_file


class TestConfigSetCredentialsFile:
    def test_new_file_is_owner_only_in_owner_only_directory(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
        isolated_home: Path,
    ) -> None:
        result = runner.invoke(cli_entrypoint, ["v2", "config", "set", "secret-key", "secret"])

        assert result.exit_code == 0, result.output
        config_dir = isolated_home / ".backend.ai"
        assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE((config_dir / "credentials.toml").stat().st_mode) == 0o600

    def test_loose_existing_file_is_tightened_and_keeps_values(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
        loose_credentials_file: Path,
    ) -> None:
        result = runner.invoke(cli_entrypoint, ["v2", "config", "set", "secret-key", "secret"])

        assert result.exit_code == 0, result.output
        assert stat.S_IMODE(loose_credentials_file.stat().st_mode) == 0o600
        assert "existing-access-key" in loose_credentials_file.read_text()


class TestProfileFiles:
    def test_profile_create_makes_every_directory_owner_only(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
        isolated_home: Path,
    ) -> None:
        result = runner.invoke(cli_entrypoint, ["v2", "profile", "create", "staging"])

        assert result.exit_code == 0, result.output
        directory_modes = {
            directory: stat.S_IMODE((isolated_home / directory).stat().st_mode)
            for directory in (
                ".backend.ai",
                ".backend.ai/profiles",
                ".backend.ai/profiles/staging",
            )
        }
        assert directory_modes == {
            ".backend.ai": 0o700,
            ".backend.ai/profiles": 0o700,
            ".backend.ai/profiles/staging": 0o700,
        }

    def test_profile_credentials_file_is_owner_only(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
        isolated_home: Path,
    ) -> None:
        runner.invoke(cli_entrypoint, ["v2", "profile", "create", "staging"])

        result = runner.invoke(
            cli_entrypoint,
            ["v2", "--profile", "staging", "config", "set", "secret-key", "secret"],
        )

        assert result.exit_code == 0, result.output
        credentials_file = isolated_home / ".backend.ai/profiles/staging/credentials.toml"
        assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600
