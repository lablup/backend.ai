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

from ai.backend.agent.errors.agent import ContainerConfinementFailedError
from ai.backend.agent.rootless.base import SelfHostedRootlessRuntime

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
    SelfHostedRootlessRuntime._write_cgroup_limits(cgroup, spec)
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
    def test_an_undelegated_controller_fails_the_apply(self, cgroup: Path) -> None:
        """A controller only has files in the leaf if the parent delegated it, and cgroupfs will
        not let anyone create the missing ones — modelled here by a directory that accepts writes
        to existing files but no new ones.

        This used to apply the rest and carry on, on the reasoning that losing the CPU pinning beats
        losing the memory limit as collateral. Both are worse than the third option, which is what
        it does now: not starting a kernel whose allocation is a fiction. The caller confines while
        the container is still held at its gate, so nothing of the user's command has run.
        """
        (cgroup / "cpuset.cpus").unlink()
        cgroup.chmod(0o500)
        try:
            with pytest.raises(ContainerConfinementFailedError, match=r"cpuset\.cpus"):
                _apply(cgroup, cpuset_cpus="0-1", memory_limit=_GIB)
            # and the limits that could be written still were — the raise comes after the loop
            assert (cgroup / "memory.max").read_text() == str(_GIB)
        finally:
            cgroup.chmod(0o700)

    def test_a_cgroup_that_vanished_fails_too(self, tmp_path: Path) -> None:
        """The container can die between creating the cgroup and writing its limits. That used to
        be tolerated so startup would not abort "over a container that is already gone" — but a
        create_task that returns a handle for a dead container is the worse answer, and the caller
        now reaps and cleans up on the way out."""
        with pytest.raises(ContainerConfinementFailedError, match=r"memory\.max"):
            SelfHostedRootlessRuntime._write_cgroup_limits(
                tmp_path / "gone", {"memory_limit": _GIB}
            )

    def test_an_empty_spec_writes_nothing(self, cgroup: Path) -> None:
        assert _apply(cgroup) == dict.fromkeys(_written(cgroup), "max")


class TestALimitThatCouldNotBeApplied:
    """A partial apply is the worst of the three outcomes.

    The kernel looks confined and is not, in whichever dimension failed — and nothing downstream can
    tell: the manager placed it here believing the limits hold, `bai admin agent search` still shows
    the slots as occupied, and the only trace used to be one warning line per file. Measured on the
    delegation failing outright: `memory.max = max`, `Cpus_allowed_list: 0-31` on a kernel allocated
    8 GiB and 4 CPUs.
    """

    def test_one_unwritable_file_fails_the_whole_apply(self, cgroup: Path) -> None:
        (cgroup / "memory.max").chmod(0o400)

        with pytest.raises(ContainerConfinementFailedError, match=r"memory\.max"):
            _apply(cgroup, memory_limit=2 * _GIB, cpuset_cpus="0-3")

    def test_the_error_names_every_limit_that_did_not_take(self, cgroup: Path) -> None:
        """One line an operator can act on, rather than one warning per file to correlate."""
        (cgroup / "memory.max").chmod(0o400)
        (cgroup / "cpuset.cpus").chmod(0o400)

        with pytest.raises(ContainerConfinementFailedError) as excinfo:
            _apply(cgroup, memory_limit=2 * _GIB, cpuset_cpus="0-3")

        assert "memory.max" in str(excinfo.value)
        assert "cpuset.cpus" in str(excinfo.value)

    def test_an_apply_with_nothing_to_write_is_not_a_failure(self, cgroup: Path) -> None:
        """A spec that asks for no limits asks for nothing; there is no dishonesty in that."""
        assert _apply(cgroup) == {
            "cpuset.cpus": "max",
            "cpuset.mems": "max",
            "memory.max": "max",
            "memory.swap.max": "max",
        }

    def test_the_limits_that_did_apply_are_still_written(self, cgroup: Path) -> None:
        """The raise comes after the loop, not out of it: the kernel is being torn down either way,
        and stopping early would leave a cgroup even less like what was asked for."""
        (cgroup / "memory.max").chmod(0o400)

        with pytest.raises(ContainerConfinementFailedError):
            _apply(cgroup, memory_limit=2 * _GIB, cpuset_cpus="0-3")

        assert (cgroup / "cpuset.cpus").read_text() == "0-3"
