from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.agent.containerd.agent import HOST_PORTS_LABEL, ContainerdAgent, _kernel_slots
from ai.backend.agent.containerd.client import ContainerRecord, TaskInfo, TaskState
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported, ProfileNotApplicable
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ContainerId,
    ContainerStatus,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    SlotName,
)

from .conftest import FakeProfile
from .fakes import FakeContainerd

TDX = SlotName("confidential.tdx")


@pytest.fixture
def agent(monkeypatch: pytest.MonkeyPatch) -> ContainerdAgent:
    """A bare agent carrying only the attributes the tested methods touch."""
    instance = object.__new__(ContainerdAgent)
    instance._runtime_profiles = []
    instance._profile_required_slots = frozenset()
    instance._runc_profile = RuncProfile(1.0)
    instance.event_producer = MagicMock()
    instance.local_config = MagicMock()
    instance.computers = {}
    instance.id = AgentId("i-test")
    instance.port_pool = PortPool((30000, 30009), cooldown_sec=0)
    instance.resource_lock = asyncio.Lock()
    instance._client = FakeContainerd()
    instance.error_monitor = MagicMock(capture_exception=AsyncMock())
    monkeypatch.setattr(instance, "reconstruct_resource_usage", AsyncMock())
    return instance


def _image(labels: dict[str, str]) -> ImageConfig:
    return cast(ImageConfig, {"canonical": "cr.example.com/stable/python:3.11", "labels": labels})


class TestResolveImageDistro:
    async def test_label_present(self, agent: ContainerdAgent) -> None:
        image = _image({"ai.backend.base-distro": "ubuntu22.04"})

        assert await agent.resolve_image_distro(image) == "ubuntu22.04"

    async def test_label_missing(self, agent: ContainerdAgent) -> None:
        with pytest.raises(UnsupportedBaseDistroError, match=r"ai\.backend\.base-distro"):
            await agent.resolve_image_distro(_image({}))

    async def test_label_empty(self, agent: ContainerdAgent) -> None:
        with pytest.raises(UnsupportedBaseDistroError):
            await agent.resolve_image_distro(_image({"ai.backend.base-distro": ""}))


class TestInitKernelContext:
    async def test_required_slot_without_accepting_profile_fails_before_distro(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        agent._runtime_profiles = [FakeProfile("coco-tdx", accepts=False)]
        agent._profile_required_slots = frozenset({TDX})
        config = cast(
            KernelCreationConfig,
            {
                **kernel_config,
                "resource_slots": {"cpu": "1", TDX: "1"},
                # no base-distro label: reaching resolve_image_distro would raise another error
                "image": _image({}),
            },
        )

        with pytest.raises(ProfileNotApplicable):
            await agent.init_kernel_context(ownership_data, MagicMock(), config)

    async def test_builtin_profile_is_selected(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        assert ctx._profile is agent._runc_profile
        assert ctx.distro == "ubuntu22.04"


class TestKernelSlots:
    def test_json_string_amounts_become_decimals(self, kernel_config: KernelCreationConfig) -> None:
        slots = _kernel_slots(kernel_config)

        assert slots == {SlotName("cpu"): Decimal(1), SlotName("mem"): Decimal(1073741824)}
        assert all(isinstance(v, Decimal) for v in slots.values())


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

    async def test_write_kernel_registry_is_a_noop(self, agent: ContainerdAgent) -> None:
        await agent._write_kernel_registry_to_recovery({}, MagicMock())

    async def test_scan_images_is_empty(self, agent: ContainerdAgent) -> None:
        result = await agent.scan_images()

        assert result.scanned_images == {}
        assert result.removed_images == {}

    async def test_check_image_is_false(self, agent: ContainerdAgent) -> None:
        assert await agent.check_image(MagicMock(), "id", AutoPullBehavior.DIGEST) is False

    async def test_restart_store_config_is_a_noop(self, agent: ContainerdAgent) -> None:
        await agent.restart_kernel__store_config(KernelId(uuid.uuid4()), "c", b"")


OWNER = "i-test"


def _add_container(
    fake: FakeContainerd,
    container_id: str,
    *,
    state: TaskState | None,
    owner: str = OWNER,
    kernel_id: uuid.UUID | None = None,
    session_id: str | None = "session-1",
    host_ports: str = "30000,30001",
) -> KernelId:
    kid = kernel_id or uuid.uuid4()
    labels = {
        "ai.backend.owner": owner,
        "ai.backend.kernel-id": str(kid),
        HOST_PORTS_LABEL: host_ports,
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
    @pytest.fixture
    def fake(self, agent: ContainerdAgent) -> FakeContainerd:
        assert isinstance(agent._client, FakeContainerd)
        return agent._client

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
        assert [(p.host, p.private_port, p.host_port) for p in container.ports] == [
            ("127.0.0.1", 30000, 30000),
            ("127.0.0.1", 30001, 30001),
        ]

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

    async def test_container_without_ports_label_has_no_ports(
        self, agent: ContainerdAgent, fake: FakeContainerd
    ) -> None:
        _add_container(fake, "c1", state=TaskState.RUNNING, host_ports="")

        [(_, container)] = await agent.enumerate_containers()

        assert container.ports == []


class TestDestroyKernel:
    async def test_without_a_container_id_nothing_happens(self, agent: ContainerdAgent) -> None:
        await agent.destroy_kernel(KernelId(uuid.uuid4()), None)

        assert cast(FakeContainerd, agent._client).calls == []

    async def test_running_container_is_stopped(self, agent: ContainerdAgent) -> None:
        fake = cast(FakeContainerd, agent._client)
        _add_container(fake, "c1", state=TaskState.RUNNING)

        await agent.destroy_kernel(KernelId(uuid.uuid4()), ContainerId("c1"))

        assert ("kill_task:SIGINT", "c1") in fake.calls
        assert "c1" not in fake.tasks

    async def test_unknown_container_is_tolerated_and_resources_are_reconstructed(
        self, agent: ContainerdAgent
    ) -> None:
        await agent.destroy_kernel(KernelId(uuid.uuid4()), ContainerId("absent"))

        cast(AsyncMock, agent.reconstruct_resource_usage).assert_awaited_once()

    async def test_containerd_error_is_captured_not_raised(self, agent: ContainerdAgent) -> None:
        fake = cast(FakeContainerd, agent._client)
        _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.failing.add("kill_task:SIGINT")

        await agent.destroy_kernel(KernelId(uuid.uuid4()), ContainerId("c1"))

        cast(AsyncMock, agent.error_monitor.capture_exception).assert_awaited_once()


class TestCleanKernel:
    @pytest.fixture
    def scratch_root(self, agent: ContainerdAgent, tmp_path: Path) -> Path:
        config = cast(MagicMock, agent.local_config)
        config.container.scratch_root = tmp_path
        config.debug.skip_container_deletion = False
        return tmp_path

    @pytest.fixture
    def collected(self, agent: ContainerdAgent, monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
        chunks: list[bytes] = []

        async def collect_logs(kernel_id: KernelId, container_id: str, iterator: Any) -> None:
            async for chunk in iterator:
                chunks.append(chunk)

        monkeypatch.setattr(agent, "collect_logs", collect_logs)
        return chunks

    async def test_works_with_an_empty_kernel_registry(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.snapshots["c1"] = []
        scratch = scratch_root / str(kid)
        scratch.mkdir()
        (scratch / "task.log").write_bytes(b"hello\n")

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert fake.containers == {} and fake.tasks == {} and fake.snapshots == {}
        assert not scratch.exists()
        assert b"".join(collected) == b"hello\n"

    async def test_unknown_container_is_tolerated(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        await agent.clean_kernel(KernelId(uuid.uuid4()), ContainerId("absent"), False)

    async def test_without_a_container_id_only_the_scratch_is_removed(
        self, agent: ContainerdAgent, scratch_root: Path
    ) -> None:
        kid = KernelId(uuid.uuid4())
        (scratch_root / str(kid)).mkdir()

        await agent.clean_kernel(kid, None, False)

        assert not (scratch_root / str(kid)).exists()
        assert cast(FakeContainerd, agent._client).calls == []

    async def test_restart_keeps_the_scratch(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.STOPPED)
        (scratch_root / str(kid)).mkdir()

        await agent.clean_kernel(kid, ContainerId("c1"), True)

        assert (scratch_root / str(kid)).exists()
        assert fake.containers == {}

    async def test_debug_flag_keeps_the_container(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        cast(MagicMock, agent.local_config).debug.skip_container_deletion = True
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.STOPPED)

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert "c1" in fake.containers

    async def test_containerd_error_does_not_stop_the_scratch_removal(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.STOPPED)
        fake.failing.add("delete_container")
        (scratch_root / str(kid)).mkdir()

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert not (scratch_root / str(kid)).exists()


class TestShutdown:
    async def test_client_is_closed_even_if_the_base_shutdown_fails(
        self, agent: ContainerdAgent, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.shutdown", side_effect=RuntimeError("boom")
        )

        with pytest.raises(RuntimeError, match="boom"):
            await agent.shutdown(MagicMock())

        assert cast(FakeContainerd, agent._client).closed


class TestAinit:
    async def test_client_connects_before_the_base_scan_runs(
        self, agent: ContainerdAgent, mocker: MockerFixture
    ) -> None:
        order: list[str] = []
        cast(MagicMock, agent.local_config).containerd = ContainerdConfig.model_validate({
            "namespace": "ns1"
        })
        connect = AsyncMock(side_effect=lambda: order.append("connect"))
        agent._client = cast(Any, MagicMock(connect=connect))
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.__ainit__",
            new=AsyncMock(side_effect=lambda: order.append("base")),
        )

        await agent.__ainit__()

        assert order == ["connect", "base"]
        connect.assert_awaited_once()

    async def test_enumerate_before_connect_returns_nothing(self, agent: ContainerdAgent) -> None:
        fake = cast(FakeContainerd, agent._client)
        fake.connected = False

        assert await agent.enumerate_containers() == []
        assert fake.calls == []
