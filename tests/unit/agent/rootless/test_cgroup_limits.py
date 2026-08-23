"""The cgroup files a kernel's allocation is written into.

enroot has no cgroup integration, so the runtime writes the leaf itself. Nothing validates what
lands there: an over-generous limit is not an error, it is just a kernel that can use more of the
node than it was allocated, which only shows up as a noisy neighbour much later.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.rootless.base import RootlessOciRuntime

_GIB = 1024**3


@pytest.fixture
def cgroup(tmp_path: Path) -> Path:
    """A leaf with the controller files a delegated cgroup-v2 directory would have."""
    leaf = tmp_path / "cgroup"
    leaf.mkdir()
    for name in ("cpuset.cpus", "cpuset.mems", "memory.max", "memory.swap.max"):
        (leaf / name).write_text("max")
    return leaf


def _written(cgroup: Path) -> dict[str, str]:
    return {p.name: p.read_text() for p in cgroup.iterdir()}


def _apply(cgroup: Path, **spec: Any) -> dict[str, str]:
    RootlessOciRuntime._write_cgroup_limits(cgroup, spec)
    return _written(cgroup)


class TestMemory:
    def test_swap_max_is_swap_alone(self, cgroup: Path) -> None:
        """The one piece of real arithmetic here. OCI and Docker count `memory_swap` as
        memory+swap COMBINED; cgroup v2's `memory.swap.max` is swap ALONE. Writing the combined
        figure straight through silently grants the container its entire memory limit a second
        time, as swap."""
        written = _apply(cgroup, memory_limit=2 * _GIB, memory_swap=3 * _GIB)

        assert written["memory.max"] == str(2 * _GIB)
        assert written["memory.swap.max"] == str(_GIB)

    def test_swap_disabled_when_the_two_are_equal(self, cgroup: Path) -> None:
        """Docker's way of spelling 'no swap' is memory_swap == memory_limit."""
        written = _apply(cgroup, memory_limit=2 * _GIB, memory_swap=2 * _GIB)

        assert written["memory.swap.max"] == "0"

    def test_a_swap_below_the_limit_does_not_go_negative(self, cgroup: Path) -> None:
        """`memory.swap.max` takes a non-negative number or `max`; a negative would be EINVAL and
        leave the previous value in place — i.e. unlimited swap."""
        written = _apply(cgroup, memory_limit=4 * _GIB, memory_swap=_GIB)

        assert written["memory.swap.max"] == "0"

    def test_swap_is_left_alone_without_a_memory_limit(self, cgroup: Path) -> None:
        """The combined figure is meaningless on its own, so there is nothing to derive."""
        written = _apply(cgroup, memory_swap=3 * _GIB)

        assert written["memory.swap.max"] == "max"


class TestCpuset:
    def test_the_allocated_cpus_and_mems(self, cgroup: Path) -> None:
        written = _apply(cgroup, cpuset_cpus="0-3,8", cpuset_mems="0")

        assert written["cpuset.cpus"] == "0-3,8"
        assert written["cpuset.mems"] == "0"

    def test_an_absent_allocation_is_not_written(self, cgroup: Path) -> None:
        """An empty cpuset.cpus is not 'no restriction', it is a cgroup no task can be moved into
        — so an unset allocation must leave the inherited value alone rather than blank it."""
        written = _apply(cgroup, cpuset_cpus="")

        assert written["cpuset.cpus"] == "max"


class TestResilience:
    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores the directory permission")
    def test_an_undelegated_controller_does_not_stop_the_rest(self, cgroup: Path) -> None:
        """A controller only has files in the leaf if the parent delegated it, and cgroupfs will
        not let anyone create the missing ones — modelled here by a directory that accepts writes
        to existing files but no new ones. Losing the memory limit as collateral would be far worse
        than losing the CPU pinning."""
        (cgroup / "cpuset.cpus").unlink()
        cgroup.chmod(0o500)
        try:
            written = _apply(cgroup, cpuset_cpus="0-1", memory_limit=_GIB)
        finally:
            cgroup.chmod(0o700)

        assert "cpuset.cpus" not in written
        assert written["memory.max"] == str(_GIB)

    def test_a_cgroup_that_vanished_is_not_an_error(self, tmp_path: Path) -> None:
        """The container can die between creating the cgroup and writing its limits, and the sweep
        reclaims empty ones. Raising here would abort container startup over a container that is
        already gone."""
        RootlessOciRuntime._write_cgroup_limits(tmp_path / "gone", {"memory_limit": _GIB})

    def test_an_empty_spec_writes_nothing(self, cgroup: Path) -> None:
        assert _apply(cgroup) == dict.fromkeys(_written(cgroup), "max")
