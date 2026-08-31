"""Scratch directories left behind by an agent that died before it could clean up.

`clean_kernel` tears the scratch down, and like every other reclaim it only runs while the agent is
alive to run it. Measured on the testbed with no session running: 12, 11 and 19 directories on the
three backends.

A scratch is the kernel's `/home/work`, which makes this the one sweep that can destroy something a
person would miss. So it asks three independent sources and removes only what all three call dead —
these tests are mostly about the cases it must NOT touch.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd import agent as agent_mod
from ai.backend.agent.containerd.agent import ContainerdAgent


class _Runtime:
    def __init__(self, containers: list[str] | Exception) -> None:
        self._containers = containers

    async def list_containers(self) -> list[str]:
        if isinstance(self._containers, Exception):
            raise self._containers
        return self._containers


class _Agent:
    """Only what the sweep touches."""

    def __init__(self, scratch_root: Path, containers: list[str] | Exception | None = None) -> None:
        self.local_config = cast(
            Any, type("C", (), {"container": type("K", (), {"scratch_root": scratch_root})()})()
        )
        self._runtime = _Runtime([] if containers is None else containers)
        self.kernel_registry: dict[Any, Any] = {}
        self.destroyed: list[str] = []

    async def _destroy_scratch(self, kernel_id: Any) -> None:
        self.destroyed.append(str(kernel_id))


async def _sweep(agent: _Agent, monkeypatch: pytest.MonkeyPatch, cgroups: Path) -> list[str]:
    monkeypatch.setattr(agent_mod, "container_cgroup_fs_path", lambda cid: cgroups / cid)
    await ContainerdAgent._sweep_orphan_scratches(cast(Any, agent))
    return agent.destroyed


@pytest.fixture
def cgroups(tmp_path: Path) -> Path:
    root = tmp_path / "cgroup"
    root.mkdir()
    return root


@pytest.fixture
def scratches(tmp_path: Path) -> Path:
    root = tmp_path / "scratches"
    root.mkdir()
    return root


def _scratch(root: Path, name: str) -> Path:
    d = root / name
    d.mkdir()
    (d / "work").write_text("a file someone would miss")
    return d


class TestWhatIsRemoved:
    async def test_a_scratch_no_source_calls_alive(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dead = str(uuid.uuid4())
        _scratch(scratches, dead)
        agent = _Agent(scratches)

        assert await _sweep(agent, monkeypatch, cgroups) == [dead]


class TestWhatIsLeftAlone:
    """Any one source saying "alive" is enough. A false negative costs a directory until the next
    restart; a false positive costs a running session its working files."""

    async def test_the_kernel_registry_knows_it(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        kid = uuid.uuid4()
        _scratch(scratches, str(kid))
        agent = _Agent(scratches)
        agent.kernel_registry[kid] = object()

        assert await _sweep(agent, monkeypatch, cgroups) == []

    async def test_the_runtime_still_lists_the_container(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The source that does not depend on our own records at all."""
        kid = str(uuid.uuid4())
        _scratch(scratches, kid)
        agent = _Agent(scratches, containers=[kid])

        assert await _sweep(agent, monkeypatch, cgroups) == []

    async def test_processes_are_still_in_its_cgroup(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        kid = str(uuid.uuid4())
        _scratch(scratches, kid)
        (cgroups / kid).mkdir()
        (cgroups / kid / "cgroup.procs").write_text("4242\n")
        agent = _Agent(scratches)

        assert await _sweep(agent, monkeypatch, cgroups) == []

    async def test_a_directory_that_is_not_a_kernel_id(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Whatever else an operator keeps under the scratch root is not ours to remove."""
        _scratch(scratches, "not-a-uuid")
        agent = _Agent(scratches)

        assert await _sweep(agent, monkeypatch, cgroups) == []

    async def test_the_memory_scratchs_tmp_sibling(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`<id>_tmp` is a live tmpfs mount that goes down with its owner, not on its own."""
        kid = str(uuid.uuid4())
        _scratch(scratches, f"{kid}_tmp")
        agent = _Agent(scratches)

        assert await _sweep(agent, monkeypatch, cgroups) == []

    async def test_a_runtime_that_cannot_be_asked_stops_the_sweep(
        self, scratches: Path, cgroups: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Losing one of the three sources means the remaining two are not enough to delete on."""
        _scratch(scratches, str(uuid.uuid4()))
        agent = _Agent(scratches, containers=ConnectionError("runtime is down"))

        assert await _sweep(agent, monkeypatch, cgroups) == []
