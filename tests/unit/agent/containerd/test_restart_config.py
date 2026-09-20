"""Docker-parity coverage for the config round-trip a kernel restart depends on.

``restart_kernel__store_config`` / ``…__load_config`` are how a restart preserves the files the
kernel was created with — ``resource.txt`` above all, which pins the cpuset and the accelerator
devices the kernel's processes are already running on. The Docker backend has carried this pair
since before the containerd backend existed; containerd reimplemented it against the scratch path
directly (``asyncio.to_thread`` instead of an executor, and no ``.resolve()`` on the scratch root),
and neither side had a test.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.common.types import KernelId


def _agent(scratch_root: Path) -> ContainerdAgent:
    agent = ContainerdAgent.__new__(ContainerdAgent)
    agent.local_config = cast(
        Any, SimpleNamespace(container=SimpleNamespace(scratch_root=scratch_root))
    )
    return agent


def _prepared_kernel(scratch_root: Path) -> KernelId:
    """A kernel whose scratch has been through ``prepare_scratch`` — i.e. ``config/`` exists."""
    kernel_id = KernelId(uuid.uuid4())
    (scratch_root / str(kernel_id) / "config").mkdir(parents=True)
    return kernel_id


class TestRestartConfigRoundTrip:
    async def test_what_was_stored_is_what_is_loaded(self, tmp_path: Path) -> None:
        agent = _agent(tmp_path)
        kernel_id = _prepared_kernel(tmp_path)

        await agent.restart_kernel__store_config(kernel_id, "resource.txt", b"cpuset=0-1\n")

        assert await agent.restart_kernel__load_config(kernel_id, "resource.txt") == b"cpuset=0-1\n"

    async def test_the_bytes_are_not_transcoded(self, tmp_path: Path) -> None:
        """The pair is declared over ``bytes``, and environ/dotfile payloads are not all UTF-8.
        Anything that decodes on the way through would corrupt them silently."""
        agent = _agent(tmp_path)
        kernel_id = _prepared_kernel(tmp_path)
        payload = b"\x00\xff\xfe binary \r\n\x80"

        await agent.restart_kernel__store_config(kernel_id, "environ.txt", payload)

        assert await agent.restart_kernel__load_config(kernel_id, "environ.txt") == payload

    async def test_storing_again_replaces_rather_than_appends(self, tmp_path: Path) -> None:
        """A restart stores the config it is restarting *with*. Appending would leave the old
        allocation in the file ahead of the new one, and resource.txt is parsed from the top."""
        agent = _agent(tmp_path)
        kernel_id = _prepared_kernel(tmp_path)

        await agent.restart_kernel__store_config(kernel_id, "resource.txt", b"cpuset=0-3\n")
        await agent.restart_kernel__store_config(kernel_id, "resource.txt", b"cpuset=4\n")

        assert await agent.restart_kernel__load_config(kernel_id, "resource.txt") == b"cpuset=4\n"

    async def test_each_kernel_keeps_its_own_config(self, tmp_path: Path) -> None:
        """The path is per-kernel; a co-located kernel restarting must not overwrite the
        allocation of the one next to it."""
        agent = _agent(tmp_path)
        first = _prepared_kernel(tmp_path)
        second = _prepared_kernel(tmp_path)

        await agent.restart_kernel__store_config(first, "resource.txt", b"cpuset=0\n")
        await agent.restart_kernel__store_config(second, "resource.txt", b"cpuset=1\n")

        assert await agent.restart_kernel__load_config(first, "resource.txt") == b"cpuset=0\n"
        assert await agent.restart_kernel__load_config(second, "resource.txt") == b"cpuset=1\n"


class TestRestartConfigWhenTheScratchIsNotThere:
    async def test_loading_a_config_that_was_never_stored_raises(self, tmp_path: Path) -> None:
        """It must not answer an absent config with empty bytes: a restart that silently loses
        resource.txt re-derives the allocation and can move the kernel off its own cpuset."""
        agent = _agent(tmp_path)
        kernel_id = _prepared_kernel(tmp_path)

        with pytest.raises(FileNotFoundError):
            await agent.restart_kernel__load_config(kernel_id, "resource.txt")

    async def test_storing_before_the_scratch_exists_raises(self, tmp_path: Path) -> None:
        """Neither backend creates ``config/`` here — ``prepare_scratch`` owns that. The failure
        must surface rather than be papered over, or the store looks like it worked and the
        matching load fails later, at restart time."""
        agent = _agent(tmp_path)
        kernel_id = KernelId(uuid.uuid4())  # deliberately NOT prepared

        with pytest.raises(FileNotFoundError):
            await agent.restart_kernel__store_config(kernel_id, "resource.txt", b"cpuset=0\n")
