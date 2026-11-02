from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.client import ContainerRecord, TaskInfo, TaskState
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ContainerId,
    ContainerStatus,
    KernelId,
)

from .fakes import FakeContainerd


@pytest.fixture
def agent(fake: FakeContainerd) -> ContainerdAgent:
    """A bare agent carrying only the attributes the tested methods touch."""
    instance = object.__new__(ContainerdAgent)
    instance.local_config = MagicMock()
    instance.id = AgentId("i-test")
    instance._client = cast(Any, fake)
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
    ("resolve_image_distro", (MagicMock(),)),
    ("check_image", (MagicMock(), "id", AutoPullBehavior.DIGEST)),
    ("init_kernel_context", (MagicMock(), MagicMock(), MagicMock())),
    ("destroy_kernel", (KernelId(uuid.uuid4()), ContainerId("c"))),
    ("clean_kernel", (KernelId(uuid.uuid4()), ContainerId("c"), False)),
    ("restart_kernel__store_config", (KernelId(uuid.uuid4()), "cfg", b"")),
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

    async def test_write_kernel_registry_is_a_noop(self, agent: ContainerdAgent) -> None:
        await agent._write_kernel_to_recovery(MagicMock())

    async def test_scan_images_is_empty(self, agent: ContainerdAgent) -> None:
        result = await agent.scan_images()

        assert result.scanned_images == {}
        assert result.removed_images == {}


OWNER = "i-test"


def _add_container(
    fake: FakeContainerd,
    container_id: str,
    *,
    state: TaskState | None,
    owner: str = OWNER,
    kernel_id: uuid.UUID | None = None,
    session_id: str | None = "session-1",
) -> KernelId:
    kid = kernel_id or uuid.uuid4()
    labels = {
        "ai.backend.owner": owner,
        "ai.backend.kernel-id": str(kid),
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
        assert container.labels["ai.backend.session-id"] == "session-1"
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
            (TaskState.UNKNOWN, ContainerStatus.DEAD),
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

    async def test_shutdown_after_a_failed_connect_still_closes_the_client(
        self, agent: ContainerdAgent, fake: FakeContainerd, mocker: MockerFixture
    ) -> None:
        fake.connected = False
        mocker.patch("ai.backend.agent.agent.AbstractAgent.shutdown", new=AsyncMock())

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

    async def test_enumerate_before_connect_returns_nothing(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        fake.connected = False

        assert await agent.enumerate_containers() == []
        assert fake.calls == []
