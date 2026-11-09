from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.agent.containerd.agent import KERNEL_IP_LABEL, ContainerdAgent
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.rpc.types import ContainerRecord, TaskInfo, TaskState
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.port_pool import PortPool
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    KernelId,
)

from .fakes import FakeCommandRunner, FakeContainerd


@pytest.fixture
def agent(
    fake: FakeContainerd,
    network: KernelNetwork,
    runner: FakeCommandRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> ContainerdAgent:
    """A bare agent carrying only the attributes the tested methods touch."""
    instance = object.__new__(ContainerdAgent)
    instance.local_config = MagicMock()
    instance.local_config.container.scratch_root = tmp_path
    instance.id = AgentId("i-test")
    instance.resource_lock = asyncio.Lock()
    instance._client = cast(Any, fake)
    instance._network = network
    instance._profile = RuncProfile()
    instance.port_pool = PortPool((30000, 30009), cooldown_sec=0)
    instance.error_monitor = MagicMock(capture_exception=AsyncMock())
    monkeypatch.setattr(instance, "reconstruct_resource_usage", AsyncMock())
    runner.script(["ip", "-d", "link", "show"], "3: bai0: <UP>\n    bridge forward_delay 1\n")
    return instance


_RAISING: list[tuple[str, tuple[Any, ...]]] = [
    ("pull_image", (MagicMock(), MagicMock())),
    ("push_image", (MagicMock(), MagicMock())),
    ("purge_images", (MagicMock(),)),
    ("restart_kernel__load_config", (KernelId(uuid.uuid4()), "cfg")),
    ("create_local_network", ("net",)),
    ("destroy_local_network", ("net",)),
    ("get_cgroup_path", (MagicMock(), ContainerId("c"))),
    ("extract_image_command", ("img",)),
]


class TestContainerdAgentVerbs:
    @pytest.mark.parametrize(("method", "args"), _RAISING, ids=[r[0] for r in _RAISING])
    async def test_unsupported_verbs_raise(
        self, agent: ContainerdAgent, method: str, args: tuple[Any, ...]
    ) -> None:
        kwargs: dict[str, Any] = {"timeout_seconds": None} if method == "pull_image" else {}

        with pytest.raises(KernelVerbNotSupported, match=method):
            await getattr(agent, method)(*args, **kwargs)

    def test_get_cgroup_version_raises(self, agent: ContainerdAgent) -> None:
        with pytest.raises(KernelVerbNotSupported, match="get_cgroup_version"):
            agent.get_cgroup_version()

    async def test_load_kernel_registry_is_empty(self, agent: ContainerdAgent) -> None:
        assert await agent._load_kernel_registry_from_recovery() == {}

    async def test_scan_images_is_empty(self, agent: ContainerdAgent) -> None:
        result = await agent.scan_images()

        assert result.scanned_images == {}
        assert result.removed_images == {}


OWNER = "i-test"
SESSION_ID = str(uuid.uuid4())


def _add_container(
    fake: FakeContainerd,
    container_id: str,
    *,
    state: TaskState | None,
    owner: str = OWNER,
    kernel_id: uuid.UUID | None = None,
    session_id: str | None = SESSION_ID,
    extra_labels: Mapping[str, str] | None = None,
) -> KernelId:
    kid = kernel_id or uuid.uuid4()
    labels = {
        "ai.backend.owner": owner,
        "ai.backend.kernel-id": str(kid),
        **(extra_labels or {}),
    }
    if session_id is not None:
        labels["ai.backend.session-id"] = session_id
    fake.containers[container_id] = ContainerRecord(
        id=container_id,
        image="img:1",
        snapshotter="overlayfs",
        snapshot_key=container_id,
        labels=labels,
    )
    if state is not None:
        fake.tasks[container_id] = TaskInfo(pid=1, state=state, exit_status=0)
    return KernelId(kid)


class TestEnumerateContainers:
    async def test_running_container_is_mapped(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        kid = _add_container(fake, "c1", state=TaskState.RUNNING)

        [(found_kid, container)] = await agent.enumerate_containers()

        assert found_kid == kid
        assert container.id == ContainerId("c1")
        assert container.status == ContainerStatus.RUNNING
        assert container.image == "img:1"
        assert container.labels["ai.backend.session-id"] == SESSION_ID
        assert container.ports == []

    async def test_stopped_container_is_exited_and_hidden_from_the_active_filter(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "c1", state=TaskState.STOPPED)

        assert await agent.enumerate_containers() == []
        [(_, container)] = await agent.enumerate_containers(ContainerStatus.dead_set())
        assert container.status == ContainerStatus.EXITED

    async def test_container_without_a_task_is_exited(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "c1", state=None)

        [(_, container)] = await agent.enumerate_containers(ContainerStatus.dead_set())

        assert container.status == ContainerStatus.EXITED

    @pytest.mark.parametrize(
        ("state", "status"),
        [
            (TaskState.CREATED, ContainerStatus.CREATED),
            (TaskState.PAUSED, ContainerStatus.PAUSED),
            (TaskState.PAUSING, ContainerStatus.PAUSED),
        ],
    )
    async def test_task_states_map_to_container_statuses(
        self,
        agent: ContainerdAgent,
        fake: FakeContainerd,
        state: TaskState,
        status: ContainerStatus,
    ) -> None:
        _add_container(fake, "c1", state=state)

        [(_, container)] = await agent.enumerate_containers(frozenset(ContainerStatus))

        assert container.status == status

    async def test_only_own_containers_are_listed(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "mine", state=TaskState.RUNNING)
        _add_container(fake, "theirs", state=TaskState.RUNNING, owner="i-other")

        listed = await agent.enumerate_containers()

        assert [c.id for _, c in listed] == [ContainerId("mine")]

    async def test_unknown_task_state_is_skipped(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "slow", state=TaskState.UNKNOWN)
        _add_container(fake, "ok", state=TaskState.RUNNING)

        listed = await agent.enumerate_containers(frozenset(ContainerStatus))

        assert [c.id for _, c in listed] == [ContainerId("ok")]

    async def test_failing_get_task_skips_only_that_container(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "bad", state=TaskState.RUNNING)
        _add_container(fake, "ok", state=TaskState.RUNNING)
        fake.failing_tasks.add("bad")

        listed = await agent.enumerate_containers()

        assert [c.id for _, c in listed] == [ContainerId("ok")]

    async def test_foreign_container_returned_despite_the_filter_is_dropped(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "mine", state=TaskState.RUNNING)
        _add_container(fake, "theirs", state=TaskState.RUNNING, owner="i-other")
        fake.ignore_filters = True

        listed = await agent.enumerate_containers()

        assert [c.id for _, c in listed] == [ContainerId("mine")]

    async def test_container_without_a_valid_kernel_id_is_skipped(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.containers["c1"] = ContainerRecord(
            id="c1",
            image="img:1",
            snapshotter="overlayfs",
            snapshot_key="c1",
            labels={"ai.backend.owner": OWNER, "ai.backend.kernel-id": "not-a-uuid"},
        )

        assert await agent.enumerate_containers() == []


class TestDestroyAndClean:
    async def test_unknown_container_reconstructs_resource_usage(
        self, agent: ContainerdAgent
    ) -> None:
        await agent.destroy_kernel(KernelId(uuid.uuid4()), ContainerId("absent"))

        cast(AsyncMock, agent.reconstruct_resource_usage).assert_awaited_once()

    async def test_destroy_then_clean_removes_everything(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        cast(MagicMock, agent.local_config).debug.skip_container_deletion = False
        kid = _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.snapshots["c1"] = []

        await agent.destroy_kernel(kid, ContainerId("c1"))
        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert fake.containers == {} and fake.tasks == {} and fake.snapshots == {}
        cast(AsyncMock, agent.reconstruct_resource_usage).assert_not_awaited()

    async def test_signature_directory_is_removed(
        self, agent: ContainerdAgent, fake: FakeContainerd, tmp_path: Path
    ) -> None:
        kid = _add_container(fake, "c1", state=TaskState.STOPPED)
        (tmp_path / str(kid)).mkdir()
        (tmp_path / str(kid) / "spec.jws").write_bytes(b"a.b.c")

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert not (tmp_path / str(kid)).exists()

    async def test_containerd_errors_are_swallowed(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        cast(MagicMock, agent.local_config).debug.skip_container_deletion = False
        kid = _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.failing.update({"kill_task:SIGTERM", "delete_container"})

        await agent.destroy_kernel(kid, ContainerId("c1"))
        await agent.clean_kernel(kid, ContainerId("c1"), False)

        cast(AsyncMock, agent.error_monitor.capture_exception).assert_awaited_once()


class TestKernelNetwork:
    async def test_clean_kernel_tears_the_network_down(
        self, agent: ContainerdAgent, runner: FakeCommandRunner
    ) -> None:
        kid = KernelId(uuid.uuid4())
        runner.script(["ip", "netns", "list"], f"bai0-{kid}\n")

        await agent.clean_kernel(kid, None, False)

        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", f"bai0-{kid}")]

    async def test_sweep_keeps_live_kernels_and_their_addresses(
        self, agent: ContainerdAgent, fake: FakeContainerd, runner: FakeCommandRunner
    ) -> None:
        live = _add_container(
            fake, "c1", state=TaskState.RUNNING, extra_labels={KERNEL_IP_LABEL: "172.30.0.2"}
        )
        _add_container(
            fake, "c2", state=TaskState.RUNNING, extra_labels={KERNEL_IP_LABEL: "not-an-ip"}
        )
        stale = KernelId(uuid.uuid4())
        runner.script(["ip", "netns", "list"], f"bai0-{live}\nbai0-{stale}\nother\n")

        await agent._sweep_network()

        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", f"bai0-{stale}")]
        assert await agent._network.setup(KernelId(uuid.uuid4())) == IPv4Address("172.30.0.3")


class TestShutdown:
    async def test_client_is_closed_even_if_the_base_shutdown_fails(
        self, agent: ContainerdAgent, fake: FakeContainerd, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.shutdown", side_effect=RuntimeError("boom")
        )

        with pytest.raises(RuntimeError, match="boom"):
            await agent.shutdown(MagicMock())

        assert fake.closed


class TestAinit:
    async def test_client_connects_before_the_base_scan_runs(
        self, agent: ContainerdAgent, mocker: MockerFixture
    ) -> None:
        order: list[str] = []
        cast(MagicMock, agent.local_config).containerd = ContainerdConfig.model_validate({
            "namespace": "ns1"
        })
        connect = AsyncMock(side_effect=lambda: order.append("connect"))
        agent._client = cast(Any, MagicMock(connect=connect, connected=False))
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.__ainit__",
            new=AsyncMock(side_effect=lambda: order.append("base")),
        )

        await agent.__ainit__()

        assert order == ["connect", "base"]
        connect.assert_awaited_once()

    async def test_client_is_closed_when_the_base_init_fails_after_connect(
        self, agent: ContainerdAgent, fake: FakeContainerd, mocker: MockerFixture
    ) -> None:
        cast(MagicMock, agent.local_config).containerd = ContainerdConfig.model_validate({})
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.__ainit__", side_effect=RuntimeError("boom")
        )

        with pytest.raises(RuntimeError, match="boom"):
            await agent.__ainit__()

        assert fake.closed

    async def test_enumerate_before_connect_returns_nothing(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        fake.connected = False

        assert await agent.enumerate_containers() == []
        assert fake.calls == []
