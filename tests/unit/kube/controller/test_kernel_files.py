from __future__ import annotations

import base64
from typing import Any

import pytest

from ai.backend.kube.controller.kernel_files import KernelFiles, build_kernel_files
from ai.backend.kube.errors import InvalidSessionWorkloadError


def _build(dotfiles: list[dict[str, Any]]) -> dict[str, str]:
    return build_kernel_files(
        environ={},
        slots={},
        mounts=[],
        session_name="s",
        internal_data={"dotfiles": dotfiles},
        cluster_ssh_keypair=None,
        bootstrap_script=None,
    ).to_secret_data()


def _entries(data: dict[str, str]) -> dict[str, list[str]]:
    """Decoded path → [area, key, mode], as install.sh reads the manifest."""
    entries = {}
    for line in data["manifest"].splitlines():
        fields = line.split(" ")
        assert len(fields) == 4
        entries[base64.b64decode(fields[3]).decode()] = fields[:3]
    return entries


class TestManifest:
    def test_a_path_with_a_space_stays_one_field(self) -> None:
        entries = _entries(_build([{"path": ".my config", "perm": "644", "data": "x"}]))
        assert entries[".my config"][0] == "work"
        assert entries[".my config"][2] == "644"

    def test_a_path_with_a_newline_injects_no_line(self) -> None:
        data = _build([
            {"path": ".a\nwork f0 0755 ../config/environ.txt", "perm": "644", "data": "x"}
        ])
        entries = _entries(data)
        assert not any(path.startswith(".a") for path in entries)
        assert "../config/environ.txt" not in entries

    @pytest.mark.parametrize("perm", ["4755", "0o644", "644\n", "rwx", ""])
    def test_a_dotfile_with_an_invalid_mode_is_skipped(self, perm: str) -> None:
        assert ".vimrc" not in _entries(_build([{"path": ".vimrc", "perm": perm, "data": "x"}]))

    def test_a_reserved_dotfile_is_skipped(self) -> None:
        entries = _entries(_build([{"path": ".ssh/authorized_keys", "perm": "644", "data": "x"}]))
        assert ".ssh/authorized_keys" not in entries

    @pytest.mark.parametrize(
        ("area", "path", "mode"),
        [
            ("etc", "a", "0644"),
            ("work", "/etc/passwd", "0644"),
            ("work", "../a", "0644"),
            ("work", "a\nb", "0644"),
            ("work", "a", "4755"),
            ("work", "", "0644"),
        ],
    )
    def test_add_rejects_unsafe_files(self, area: str, path: str, mode: str) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            KernelFiles().add(area, path, "x", mode)
