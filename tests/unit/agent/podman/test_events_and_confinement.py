"""The two things podman does for this backend, and the one thing it cannot.

conmon gives us a real event stream (the self-hosted backends have to poll for container death),
and it will not put the container where the agent's stats reader looks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.errors.agent import ContainerConfinementFailedError
from ai.backend.agent.network.privnet.client import PrivNetClient
from ai.backend.agent.podman.runtime import PodmanRuntime
from ai.backend.agent.rootless import runtime as rootless_runtime


@pytest.fixture
def runtime(tmp_path: Path) -> PodmanRuntime:
    return PodmanRuntime(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=os.geteuid(),
        kernel_gid=os.getegid(),
    )


class TestTheEventStream:
    def test_a_death_carries_its_exit_code(self) -> None:
        event = PodmanRuntime._parse_event(
            b'{"Type":"container","Status":"died","Name":"c1","ContainerExitCode":137}'
        )

        assert event is not None
        assert (event.kind, event.container_id, event.exit_code) == ("exit", "c1", 137)

    def test_an_oom_is_not_reported_as_an_ordinary_exit(self) -> None:
        event = PodmanRuntime._parse_event(b'{"Type":"container","Status":"oom","Name":"c1"}')

        assert event is not None
        assert event.kind == "oom"

    @pytest.mark.parametrize(
        "line",
        [
            b'{"Type":"container","Status":"cleanup","Name":"c1"}',  # not a lifecycle transition
            b'{"Type":"container","Status":"died"}',  # no name: not a container we can act on
            b"not json at all",
        ],
    )
    def test_what_the_agent_cannot_act_on_is_dropped_rather_than_raised(self, line: bytes) -> None:
        """The stream is long-lived; one unparseable line must not end it."""
        assert PodmanRuntime._parse_event(line) is None


class TestConfinement:
    """Rootless podman resolves --cgroup-parent inside the user's own delegated subtree, so the
    container never lands in /sys/fs/cgroup/backend-ai/<kernel-id> on its own."""

    async def test_the_privnet_is_asked_when_there_is_one(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rt = PodmanRuntime(
            data_path=tmp_path / "data",
            cache_path=tmp_path / "cache",
            runtime_path=tmp_path / "run",
            state_path=tmp_path / "state",
            kernel_uid=os.geteuid(),
            kernel_gid=os.getegid(),
            privnet_socket="/run/privnet.sock",
        )
        seen: list[tuple[Any, ...]] = []

        async def _confined(self: Any, *args: Any) -> None:
            seen.append(args)

        monkeypatch.setattr(PrivNetClient, "confine_container", _confined)

        await rt._confine("c1", {"memory_limit": 1024}, 4242)

        assert [a[:3] for a in seen] == [("c1", "c1", 4242)]

    async def test_a_cgroup_v1_host_is_not_a_failure(
        self, runtime: PodmanRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(rootless_runtime, "_CGROUP_V2_MARKER", str(tmp_path / "absent"))

        await runtime._confine("c1", {"memory_limit": 1024}, 4242)

    async def test_a_container_that_cannot_be_moved_in_does_not_start(
        self, runtime: PodmanRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Starting it anyway would produce a kernel the manager believes is limited and is not."""
        marker = tmp_path / "cgroup.controllers"
        marker.write_text("cpu memory")
        monkeypatch.setattr(rootless_runtime, "_CGROUP_V2_MARKER", str(marker))
        monkeypatch.setattr(
            rootless_runtime, "container_cgroup_fs_path", lambda _cid: tmp_path / "cg"
        )

        def _refuse(*args: Any, **kwargs: Any) -> None:
            raise PermissionError(13, "Permission denied")

        monkeypatch.setattr(Path, "write_text", _refuse)

        with pytest.raises(ContainerConfinementFailedError):
            await runtime._confine("c1", {"memory_limit": 1024}, 4242)
