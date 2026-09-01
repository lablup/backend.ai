"""What happens when a kernel cannot be put in its cgroup.

The agent tells the manager how much of the node a kernel got. On these runtimes nothing enforces
that but this step: there is no daemon reading `linux.resources` out of an OCI spec, so a container
that is not moved into its own cgroup simply inherits the agent's. Measured on a kernel allocated
8 GiB and 4 CPUs with the delegation failing: `memory.max = max`, `Cpus_allowed_list: 0-31`, no
utilization reported at all, and — being in the agent's cgroup — `systemctl stop` on the agent
takes the kernel with it.

It used to log that and start the kernel anyway. These tests hold it to refusing instead, and to
leaving nothing behind when it does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.containerd.logs import rotated_paths
from ai.backend.agent.errors.agent import ContainerConfinementFailedError
from ai.backend.agent.network.privnet.client import PrivNetClient, PrivNetClientError
from ai.backend.agent.rootless import runtime as rootless_runtime
from ai.backend.agent.rootless.base import SelfHostedRootlessRuntime


class TestTheDelegationToPrivnet:
    """An unprivileged agent cannot make a cgroup under /sys/fs/cgroup, so it asks the privnet.
    When that ask fails there is no fallback — the local path cannot work either, which is why it
    was delegating in the first place."""

    @pytest.mark.parametrize(
        "failure",
        [
            ConnectionRefusedError("no privnet listening"),
            TimeoutError("privnet did not answer"),
            PrivNetClientError("privnet refused"),
        ],
        ids=["socket-gone", "timeout", "refused"],
    )
    async def test_every_way_the_privnet_can_fail_refuses_the_kernel(
        self,
        runtime: SelfHostedRootlessRuntime,
        monkeypatch: pytest.MonkeyPatch,
        failure: Exception,
    ) -> None:
        async def _fail(*args: Any, **kwargs: Any) -> None:
            raise failure

        monkeypatch.setattr(PrivNetClient, "confine_container", _fail)
        runtime._privnet_socket = "/nonexistent/privnet.sock"

        with pytest.raises(ContainerConfinementFailedError, match="privnet could not confine"):
            await runtime._confine_via_privnet("c1", {"memory_limit": 1024}, 4242)

    async def test_a_successful_delegation_passes_the_allocation_through(
        self, runtime: SelfHostedRootlessRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[tuple[Any, ...]] = []

        async def _ok(self: Any, *args: Any) -> None:
            seen.append(args)

        monkeypatch.setattr(PrivNetClient, "confine_container", _ok)
        runtime._privnet_socket = "/nonexistent/privnet.sock"

        await runtime._confine_via_privnet("c1", {"memory_limit": 1024}, 4242)

        assert [a[:3] for a in seen] == [("c1", "c1", 4242)]  # session falls back to container id
        assert seen[0][3] == {"memory.max": "1024"}


class TestTheLocalPath:
    """The agent makes the cgroup itself where it is privileged enough to."""

    def test_a_cgroup_that_cannot_be_created_refuses_the_kernel(
        self, runtime: SelfHostedRootlessRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        marker = tmp_path / "cgroup.controllers"
        marker.write_text("cpu memory")
        monkeypatch.setattr(rootless_runtime, "_CGROUP_V2_MARKER", str(marker))

        def _refuse(*args: Any, **kwargs: Any) -> None:
            raise PermissionError(13, "Permission denied")

        monkeypatch.setattr(Path, "mkdir", _refuse)

        with pytest.raises(ContainerConfinementFailedError, match="cannot create the cgroup"):
            runtime._create_cgroup("c1", {"memory_limit": 1024})

    def test_a_cgroup_v1_host_is_not_a_failure(
        self, runtime: SelfHostedRootlessRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Not a failed attempt but a standing property of the node: v1 splits every controller
        into its own hierarchy and this runtime will not half-apply limits across trees. Refusing
        here would make every kernel on such a host unstartable — a different decision from the one
        this module is making, and not one to take as a side effect of it.
        """
        monkeypatch.setattr(rootless_runtime, "_CGROUP_V2_MARKER", str(tmp_path / "absent"))

        assert runtime._create_cgroup("c1", {"memory_limit": 1024}) is None


class TestNothingIsLeftBehind:
    """By the time a container is confined it is journalled and in `_pids`, so refusing it has more
    to undo than the reap that covers the earlier steps."""

    def _half_built(self, runtime: SelfHostedRootlessRuntime) -> tuple[Path, Path]:
        container_id = "c1"
        state = runtime._state_path / container_id
        state.mkdir(parents=True, exist_ok=True)
        (state / "container.json").write_text('{"pid": 4242}')
        log = runtime._log_path(container_id)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("some output")
        rotated_paths(log)[1].write_text("older output")
        runtime._pids[container_id] = 4242
        return state, log

    async def test_the_journal_entry_the_log_and_the_pid_all_go(
        self, runtime: SelfHostedRootlessRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, log = self._half_built(runtime)
        reaped: list[str] = []

        async def _reap(cid: str) -> None:
            reaped.append(cid)

        monkeypatch.setattr(runtime, "_reap", _reap)

        await runtime._abandon_container("c1")

        assert reaped == ["c1"]
        assert not state.exists(), "a journal entry left here is recovered as a running container"
        assert not log.exists(), "nothing else ever unlinks a container log"
        assert not rotated_paths(log)[1].exists(), "the rotated files are as much the log"
        assert runtime._pids == {}

    async def test_it_is_safe_on_a_container_that_left_nothing(
        self, runtime: SelfHostedRootlessRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It runs from an `except` on any failure in that window, including ones that happen
        before the journal entry exists."""

        async def _reap(cid: str) -> None: ...

        monkeypatch.setattr(runtime, "_reap", _reap)

        await runtime._abandon_container("never-existed")
