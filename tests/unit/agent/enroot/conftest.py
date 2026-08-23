from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.enroot.runtime import EnrootRuntime


@pytest.fixture
def runtime(tmp_path: Path) -> EnrootRuntime:
    """A runtime whose four roots are all under tmp_path.

    Nothing here touches enroot, /proc or /sys/fs/cgroup: every test in this package drives a pure
    function (argv building, cgroup file contents, journal replay, log rotation, image config) and
    asserts on what it produced.
    """
    return EnrootRuntime(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=1000,
        kernel_gid=1000,
    )
