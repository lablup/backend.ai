from __future__ import annotations

import pytest

from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry


class TestVerifyPaths:
    def test_accepts_entries_under_work_dir(self) -> None:
        DotfileEntries(
            entries=(
                DotfileEntry(path=".bashrc", perm="644", data=""),
                DotfileEntry(path=".ssh/id_rsa", perm="600", data=""),
            )
        ).verify_paths()

    @pytest.mark.parametrize("path", [".ssh/authorized_keys", "/etc/passwd", "../config/x"])
    def test_rejects_any_invalid_entry(self, path: str) -> None:
        entries = DotfileEntries(
            entries=(
                DotfileEntry(path=".bashrc", perm="644", data=""),
                DotfileEntry(path=path, perm="644", data=""),
            )
        )
        with pytest.raises(InvalidDotfilePath):
            entries.verify_paths()
