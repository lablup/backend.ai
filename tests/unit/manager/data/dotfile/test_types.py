from __future__ import annotations

import pytest

from ai.backend.common import msgpack
from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.common.exception import InvalidAPIParameters
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


class TestVerifyPacked:
    @pytest.mark.parametrize(
        "packed",
        [
            b"\x90",
            msgpack.packb([{"path": ".bashrc", "perm": "644", "data": ""}]),
        ],
    )
    def test_accepts_entries_under_work_dir(self, packed: bytes) -> None:
        DotfileEntries.verify_packed(packed)

    def test_rejects_path_by_path_rule(self) -> None:
        with pytest.raises(InvalidDotfilePath):
            DotfileEntries.verify_packed(
                msgpack.packb([{"path": "/etc/passwd", "perm": "644", "data": ""}])
            )

    @pytest.mark.parametrize(
        "packed",
        [
            b"\xc1",
            b"\x91",
            b"\x90\x90",
            msgpack.packb(1),
            msgpack.packb([1]),
            msgpack.packb(["a"]),
            msgpack.packb([{"perm": "644", "data": ""}]),
            msgpack.packb([{"path": ".bashrc", "data": ""}]),
            msgpack.packb([{"path": 1, "perm": "644", "data": ""}]),
        ],
    )
    def test_rejects_malformed_data(self, packed: bytes) -> None:
        with pytest.raises(InvalidAPIParameters) as exc_info:
            DotfileEntries.verify_packed(packed)
        assert not isinstance(exc_info.value, InvalidDotfilePath)
