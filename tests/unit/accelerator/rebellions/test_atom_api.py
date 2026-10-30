import stat
from pathlib import Path

import pytest

from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI, LibraryError


def _make_tool(tmp_path: Path, body: str) -> str:
    path = tmp_path / "rbln-smi"
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


class TestATOMAPI:
    @pytest.fixture
    def payload(self, tmp_path: Path, stat_json: str) -> Path:
        path = tmp_path / "out.json"
        path.write_text(stat_json)
        return path

    async def test_get_stats_passes_stat_args(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, f'echo "$@" > {tmp_path}/args; cat {payload}')
        stats = await ATOMAPI.get_stats(tool, ("-j",))
        assert len(stats.devices) == 4
        assert (tmp_path / "args").read_text().strip() == "-j"

    async def test_get_stats_defaults_to_group_flag(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, f'echo "$@" > {tmp_path}/args; cat {payload}')
        await ATOMAPI.get_stats(tool)
        assert (tmp_path / "args").read_text().strip() == "-g -j"

    async def test_stderr_with_zero_exit_is_not_fatal(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, f"echo 'warning: x' >&2; cat {payload}")
        stats = await ATOMAPI.get_stats(tool)
        assert len(stats.devices) == 4

    async def test_nonzero_exit_raises(self, tmp_path: Path) -> None:
        tool = _make_tool(tmp_path, "echo boom >&2; exit 3")
        with pytest.raises(LibraryError, match="exit code 3"):
            await ATOMAPI.get_stats(tool)

    async def test_group_stderr_is_fatal(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, f'case "$1" in group) echo bad >&2;; *) cat {payload};; esac')
        with pytest.raises(LibraryError):
            await ATOMAPI.create_group(tool, [0, 1])

    async def test_create_group_picks_free_id(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, f'echo "$@" >> {tmp_path}/args; cat {payload}')
        assert await ATOMAPI.create_group(tool, [0, 1]) == 1
        assert "group -c 1 -a 0,1" in (tmp_path / "args").read_text()
