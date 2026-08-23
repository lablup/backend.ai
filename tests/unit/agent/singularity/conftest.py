from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.singularity.runtime import SingularityRuntime

_CID = "kernel-1"


@pytest.fixture
def runtime(tmp_path: Path) -> SingularityRuntime:
    """A runtime rooted under tmp_path, with one container already registered.

    `_launch_argv` reads the image and command tables that `create_container` fills, so a test
    that only wants the command line still needs those two entries.
    """
    rt = SingularityRuntime(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=1000,
        kernel_gid=1000,
    )
    rt._images[_CID] = "registry/py:3.12"
    rt._commands[_CID] = ["/opt/kernel/entrypoint.sh"]
    return rt
