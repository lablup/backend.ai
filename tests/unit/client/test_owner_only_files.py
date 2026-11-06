from __future__ import annotations

import stat
from pathlib import Path

import pytest

from ai.backend.client.owner_only_files import ensure_owner_only_file


@pytest.fixture
def loose_file_with_content(tmp_path: Path, world_readable_umask: None) -> Path:
    loose_file = tmp_path / "secret"
    loose_file.write_text("kept")
    loose_file.chmod(0o644)
    return loose_file


@pytest.fixture
def file_in_loose_directory(tmp_path: Path, world_readable_umask: None) -> Path:
    loose_directory = tmp_path / "shared"
    loose_directory.mkdir()
    loose_directory.chmod(0o755)
    return loose_directory / "secret"


@pytest.mark.usefixtures("world_readable_umask")
class TestEnsureOwnerOnlyFile:
    def test_new_file_is_empty_and_owner_only(self, tmp_path: Path) -> None:
        new_file = tmp_path / "secret"

        ensure_owner_only_file(new_file)

        assert stat.S_IMODE(new_file.stat().st_mode) == 0o600
        assert new_file.read_text() == ""

    def test_loose_file_is_tightened_and_keeps_content(self, loose_file_with_content: Path) -> None:
        ensure_owner_only_file(loose_file_with_content)

        assert stat.S_IMODE(loose_file_with_content.stat().st_mode) == 0o600
        assert loose_file_with_content.read_text() == "kept"

    def test_every_missing_directory_is_owner_only(self, tmp_path: Path) -> None:
        ensure_owner_only_file(tmp_path / "outer" / "inner" / "secret")

        assert stat.S_IMODE((tmp_path / "outer").stat().st_mode) == 0o700
        assert stat.S_IMODE((tmp_path / "outer" / "inner").stat().st_mode) == 0o700

    def test_existing_directory_keeps_its_mode(self, file_in_loose_directory: Path) -> None:
        ensure_owner_only_file(file_in_loose_directory)

        assert stat.S_IMODE(file_in_loose_directory.parent.stat().st_mode) == 0o755
