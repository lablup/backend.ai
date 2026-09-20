"""The OCI-spec backends' ContainerLocator, and the seam it exists to create.

The session half of SessionNetwork asks four things of the node's containers; the
lifecycle half needs a whole OciRuntime. Splitting them is what lets a backend with no OciRuntime at
all — Docker — run the same session code, so these cover what the narrow half actually answers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast, override

import pytest

from ai.backend.agent.containerd.locator import OciRuntimeLocator
from ai.backend.agent.containerd.oci import OWNER_AGENT_LABEL, SESSION_ID_LABEL
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.network.locator import ContainerLocator, LiveContainer
from ai.backend.agent.network.runtime import ContainerInfo
from ai.backend.agent.network.session_network import SessionNetwork


class _FakeRuntime:
    """Only what the locator reaches for; anything else is a bug in the locator."""

    def __init__(self, infos: Sequence[ContainerInfo] = (), pid: int | None = None) -> None:
        self.infos = list(infos)
        self.pid = pid
        self.opened = 0
        self.closed = 0

    async def open(self) -> None:
        self.opened += 1

    async def close(self) -> None:
        self.closed += 1

    async def container_pid(self, container_id: str) -> int | None:
        return self.pid

    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        return self.infos


def _info(cid: str, labels: dict[str, str]) -> ContainerInfo:
    return ContainerInfo(id=cid, image="img:1", labels=labels, status="running")


class TestWhatTheLocatorReports:
    async def test_a_labelled_container_is_reported_with_its_session(self) -> None:
        runtime = _FakeRuntime([_info("c1", {SESSION_ID_LABEL: "s1"})])
        live = await OciRuntimeLocator(cast(Any, runtime)).live_sessions()
        assert live["c1"].session_id == "s1"

    async def test_the_owning_agent_comes_back_too(self) -> None:
        # A node can run one agent per backend, so "on this node" and "mine" are different
        # questions; the caller filters on this to decide what it may reclaim.
        runtime = _FakeRuntime([
            _info("mine", {SESSION_ID_LABEL: "s1", OWNER_AGENT_LABEL: "i-a"}),
            _info("theirs", {SESSION_ID_LABEL: "s1", OWNER_AGENT_LABEL: "i-b"}),
        ])
        live = await OciRuntimeLocator(cast(Any, runtime)).live_sessions()
        assert live["mine"].owner_agent_id == "i-a"
        assert live["theirs"].owner_agent_id == "i-b"

    async def test_an_unowned_container_reports_no_owner(self) -> None:
        runtime = _FakeRuntime([_info("c1", {SESSION_ID_LABEL: "s1"})])
        live = await OciRuntimeLocator(cast(Any, runtime)).live_sessions()
        assert live["c1"].owner_agent_id is None

    async def test_a_container_that_is_not_a_kernel_is_not_reported(self) -> None:
        # Anything on the node without a session label is not ours to rebuild state from.
        runtime = _FakeRuntime([_info("stray", {"some.other": "label"})])
        assert await OciRuntimeLocator(cast(Any, runtime)).live_sessions() == {}

    async def test_the_pid_comes_from_the_runtime(self) -> None:
        runtime = _FakeRuntime(pid=4242)
        assert await OciRuntimeLocator(cast(Any, runtime)).container_pid("c1") == 4242


class TestTheConnection:
    async def test_open_and_close_reach_the_runtime(self) -> None:
        runtime = _FakeRuntime()
        locator = OciRuntimeLocator(cast(Any, runtime))
        await locator.open()
        await locator.close()
        assert (runtime.opened, runtime.closed) == (1, 1)


class TestTheCgroupPath:
    def test_it_is_bais_own_layout(self) -> None:
        # These backends write this path into their OCI spec's cgroupsPath, so the privnet creating
        # a cgroup there is creating the one the container will actually be placed in.
        locator = OciRuntimeLocator(cast(Any, _FakeRuntime()))
        assert locator.cgroup_path("c1") == container_cgroup_fs_path("c1")

    def test_a_locator_that_places_nothing_refuses(self) -> None:
        """The default, which Docker keeps: the privnet writes to this path as root, so guessing is
        worse than declining."""

        class _NoCgroups(ContainerLocator):
            @override
            async def open(self) -> None: ...

            @override
            async def container_pid(self, container_id: str) -> int | None:
                return None

            @override
            async def live_sessions(self) -> Mapping[str, LiveContainer]:
                return {}

        with pytest.raises(NotImplementedError):
            _NoCgroups().cgroup_path("c1")


class TestTheSessionNetworkSeam:
    async def test_a_separate_locator_is_used_for_the_session_half(self) -> None:
        """The point of the split: the session half must not reach the runtime at all."""

        class _Exploding(_FakeRuntime):
            @override
            async def list_container_infos(self) -> Sequence[ContainerInfo]:
                raise AssertionError("the session half must ask the locator, not the runtime")

            @override
            async def container_pid(self, container_id: str) -> int | None:
                raise AssertionError("the session half must ask the locator, not the runtime")

        class _Locator(ContainerLocator):
            @override
            async def open(self) -> None: ...

            @override
            async def container_pid(self, container_id: str) -> int | None:
                return 4242

            @override
            async def live_sessions(self) -> Mapping[str, LiveContainer]:
                return {"c1": LiveContainer(session_id="s1", owner_agent_id="i-a")}

        runtime = _Exploding()
        net = SessionNetwork(
            cast(Any, object()),
            agent_id="i-a",
            host_ip="127.0.0.1",
            runtime=cast(Any, runtime),
            cni_runner=cast(Any, object()),
            backends={},
            locator=_Locator(),
            local_subnets=cast(Any, object()),
            ipam=cast(Any, object()),
        )
        assert await net._live_containers() == {"c1": "s1"}
        assert await net._live_and_own_containers() == ({"c1": "s1"}, {"c1": "s1"})

    async def test_another_agents_container_is_seen_but_not_owned(self) -> None:
        class _Locator(ContainerLocator):
            @override
            async def open(self) -> None: ...

            @override
            async def container_pid(self, container_id: str) -> int | None:
                return None

            @override
            async def live_sessions(self) -> Mapping[str, LiveContainer]:
                return {"theirs": LiveContainer(session_id="s1", owner_agent_id="i-b")}

        net = SessionNetwork(
            cast(Any, object()),
            agent_id="i-a",
            host_ip="127.0.0.1",
            runtime=cast(Any, _FakeRuntime()),
            cni_runner=cast(Any, object()),
            backends={},
            locator=_Locator(),
            local_subnets=cast(Any, object()),
            ipam=cast(Any, object()),
        )
        live, ours = await net._live_and_own_containers()
        assert live == {"theirs": "s1"}
        assert ours == {}
