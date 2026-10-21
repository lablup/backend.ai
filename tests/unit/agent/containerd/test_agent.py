from __future__ import annotations

import asyncio
import dataclasses
import uuid
from collections.abc import Mapping
from decimal import Decimal
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.alloc_map import DiscretePropertyAllocMap
from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.agent.containerd import agent as agent_module
from ai.backend.agent.containerd.agent import HOST_PORTS_LABEL, ContainerdAgent, _kernel_slots
from ai.backend.agent.containerd.client import ContainerRecord, TaskInfo, TaskState
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.profile.base import KernelLaunch, LaunchPlan, RuntimeProfile
from ai.backend.agent.containerd.profile.loader import select_profile
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported, ProfileNotApplicable
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import ComputerContext, DeviceSlotInfo, KernelResourceSpec
from ai.backend.agent.types import Container, KernelOwnershipData
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    SlotName,
    SlotTypes,
)

from .conftest import FakeProfile
from .fakes import FakeCommandRunner, FakeContainerd

TDX = SlotName("confidential.tdx")
GPU = SlotName("cuda.shares")


@pytest.fixture
def runner() -> FakeCommandRunner:
    return FakeCommandRunner()


@pytest.fixture
def agent(monkeypatch: pytest.MonkeyPatch, runner: FakeCommandRunner) -> ContainerdAgent:
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
    instance._orphan_ports = {}
    instance._network = KernelNetwork(
        "bai-t", IPv4Network("172.30.9.0/24"), "", (30000, 30009), run=runner
    )
    instance.kernel_registry = {}
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


class _PreparingProfile(FakeProfile):
    events: list[str]
    _prepared: KernelCreationConfig | None
    _prepare_error: Exception | None
    received: list[KernelCreationConfig]

    def __init__(
        self,
        events: list[str],
        *,
        prepared: KernelCreationConfig | None = None,
        error: Exception | None = None,
    ) -> None:
        super().__init__("coco-tdx", accepts=True)
        self.events = events
        self._prepared = prepared
        self._prepare_error = error
        self.received = []

    @override
    async def prepare(self, config: KernelCreationConfig) -> KernelCreationConfig:
        self.events.append("prepare")
        self.received.append(config)
        if self._prepare_error is not None:
            raise self._prepare_error
        return self._prepared if self._prepared is not None else config


class _TwoMethodProfile:
    name = "old"

    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
        return True

    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        raise NotImplementedError


class TestInitKernelContextPrepare:
    async def test_prepare_runs_after_select_and_before_the_context(
        self,
        agent: ContainerdAgent,
        monkeypatch: pytest.MonkeyPatch,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        events: list[str] = []
        profile = _PreparingProfile(events)
        agent._runtime_profiles = [profile]

        def select(*args: Any, **kwargs: Any) -> RuntimeProfile:
            events.append("select")
            return select_profile(*args, **kwargs)

        def context(*args: Any, **kwargs: Any) -> Any:
            events.append("context")
            return MagicMock()

        monkeypatch.setattr(agent_module, "select_profile", select)
        monkeypatch.setattr(agent_module, "ContainerdKernelCreationContext", context)

        await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        assert events == ["select", "prepare", "context"]
        assert profile.received == [kernel_config]

    async def test_returned_config_reaches_the_context(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        image = cast(ImageConfig, {**kernel_config["image"], "repo_digest": "sha256:" + "a" * 64})
        prepared = cast(KernelCreationConfig, {**kernel_config, "image": image})
        profile = _PreparingProfile([], prepared=prepared)
        agent._runtime_profiles = [profile]

        ctx = await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        assert ctx.kernel_config is prepared
        assert ctx.kernel_config["image"].get("repo_digest") == "sha256:" + "a" * 64
        assert kernel_config["image"].get("repo_digest") is None

    async def test_prepare_error_propagates_and_no_context_is_built(
        self,
        agent: ContainerdAgent,
        monkeypatch: pytest.MonkeyPatch,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        agent._runtime_profiles = [_PreparingProfile([], error=ProfileNotApplicable("registry"))]
        context = MagicMock()
        monkeypatch.setattr(agent_module, "ContainerdKernelCreationContext", context)

        with pytest.raises(ProfileNotApplicable, match="registry"):
            await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        context.assert_not_called()

    async def test_two_method_profile_still_works(
        self,
        agent: ContainerdAgent,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        profile = _TwoMethodProfile()
        agent._runtime_profiles = [cast(RuntimeProfile, profile)]

        ctx = await agent.init_kernel_context(ownership_data, MagicMock(), kernel_config)

        assert ctx._profile.name == "old"
        assert ctx.kernel_config is kernel_config


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

        assert ("kill_task:SIGTERM", "c1") in fake.calls
        assert "c1" not in fake.tasks

    async def test_unknown_container_is_tolerated_and_resources_are_reconstructed(
        self, agent: ContainerdAgent
    ) -> None:
        await agent.destroy_kernel(KernelId(uuid.uuid4()), ContainerId("absent"))

        cast(AsyncMock, agent.reconstruct_resource_usage).assert_awaited_once()

    async def test_containerd_error_is_captured_not_raised(self, agent: ContainerdAgent) -> None:
        fake = cast(FakeContainerd, agent._client)
        _add_container(fake, "c1", state=TaskState.RUNNING)
        fake.failing.add("kill_task:SIGTERM")

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

    async def test_ports_of_a_container_found_at_startup_are_released_once(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        collected: list[bytes],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.RUNNING, host_ports="30000,30001")
        for port in (30000, 30001):
            agent.port_pool.discard(port)
        await agent._record_orphans()
        released: list[int] = []
        real_release = agent.port_pool.release_many

        def spy(ports: Any) -> None:
            ports = list(ports)
            released.extend(ports)
            real_release(ports)

        monkeypatch.setattr(agent.port_pool, "release_many", spy)

        await agent.clean_kernel(kid, ContainerId("c1"), False)
        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert released == [30000, 30001]
        assert agent.port_pool.used_ports() == set()

    async def test_ports_of_a_kernel_cleaned_by_the_registry_loop_are_not_released_again(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.STOPPED, host_ports="30000,30001")
        # the base released both ports with the registry entry; a new kernel took them
        in_use = {agent.port_pool.acquire(), agent.port_pool.acquire()}

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert agent.port_pool.used_ports() == in_use

    async def test_a_container_dead_at_startup_releases_no_ports(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.UNKNOWN, host_ports="30000,30001")
        in_use = {agent.port_pool.acquire(), agent.port_pool.acquire()}
        await agent._record_orphans()

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert agent.port_pool.used_ports() == in_use

    async def test_ports_of_a_registered_kernel_are_left_to_the_base(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=TaskState.STOPPED, host_ports="30000,30001")
        agent.kernel_registry[kid] = MagicMock()
        for port in (30000, 30001):
            agent.port_pool.discard(port)

        await agent.clean_kernel(kid, ContainerId("c1"), False)

        assert agent.port_pool.used_ports() == {30000, 30001}

    async def test_unknown_container_is_tolerated(
        self, agent: ContainerdAgent, scratch_root: Path, collected: list[bytes]
    ) -> None:
        await agent.clean_kernel(KernelId(uuid.uuid4()), ContainerId("absent"), False)

    async def test_without_a_container_id_the_network_and_scratch_are_removed(
        self, agent: ContainerdAgent, scratch_root: Path, runner: FakeCommandRunner
    ) -> None:
        kid = KernelId(uuid.uuid4())
        (scratch_root / str(kid)).mkdir()
        runner.script(["ip", "netns", "list"], f"bai-t-{kid}\n")

        await agent.clean_kernel(kid, None, False)

        assert not (scratch_root / str(kid)).exists()
        assert cast(FakeContainerd, agent._client).calls == []
        assert ("ip", "netns", "del", f"bai-t-{kid}") in runner.calls

    async def test_network_teardown_failure_does_not_stop_the_scratch_removal(
        self, agent: ContainerdAgent, scratch_root: Path, runner: FakeCommandRunner
    ) -> None:
        kid = KernelId(uuid.uuid4())
        (scratch_root / str(kid)).mkdir()
        runner.failing.add(("ip", "netns", "list"))

        await agent.clean_kernel(kid, None, False)

        assert not (scratch_root / str(kid)).exists()

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

    async def test_shutdown_after_a_failed_connect_still_closes_the_client(
        self, agent: ContainerdAgent, mocker: MockerFixture
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
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

    async def test_network_is_initialised_restored_and_swept_before_the_base_scan(
        self, agent: ContainerdAgent, mocker: MockerFixture
    ) -> None:
        order: list[str] = []
        cast(MagicMock, agent.local_config).containerd = ContainerdConfig.model_validate({})
        fake = cast(FakeContainerd, agent._client)
        alive = _add_container(fake, "c1", state=TaskState.RUNNING)
        record = fake.containers["c1"]
        fake.containers["c1"] = dataclasses.replace(
            record, labels={**record.labels, "ai.backend.containerd.kernel-ip": "172.30.9.2"}
        )
        network = MagicMock(
            init=AsyncMock(side_effect=lambda: order.append("init")),
            sweep=AsyncMock(side_effect=lambda ids: order.append("sweep")),
            restore=MagicMock(side_effect=lambda *a: order.append("restore")),
        )
        agent._network = network
        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.__ainit__",
            new=AsyncMock(side_effect=lambda: order.append("base")),
        )

        await agent.__ainit__()

        assert order == ["init", "restore", "sweep", "base"]
        network.restore.assert_called_once_with(alive, IPv4Address("172.30.9.2"))
        network.sweep.assert_awaited_once_with([alive])

    async def test_enumerate_before_connect_returns_nothing(self, agent: ContainerdAgent) -> None:
        fake = cast(FakeContainerd, agent._client)
        fake.connected = False

        assert await agent.enumerate_containers() == []
        assert fake.calls == []


def _gpu_context() -> ComputerContext:
    """An accelerator plugin that, like cuda_vfio, can only inspect a Docker container."""
    plugin = MagicMock()
    plugin.restore_from_container = AsyncMock(side_effect=TypeError("not a docker container"))
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("0"): DeviceSlotInfo(SlotTypes.COUNT, GPU, Decimal(1)),
            DeviceId("1"): DeviceSlotInfo(SlotTypes.COUNT, GPU, Decimal(1)),
        },
    )
    return ComputerContext(instance=plugin, devices=[], alloc_map=alloc_map)


def _add_gpu_container(
    agent: ContainerdAgent,
    tmp_path: Path,
    name: str,
    device_id: str,
    *,
    resource_txt: bool = True,
    config_label: bool = True,
) -> None:
    fake = cast(FakeContainerd, agent._client)
    _add_container(fake, name, state=TaskState.RUNNING, session_id=str(uuid.uuid4()))
    config = tmp_path / name
    config.mkdir()
    if resource_txt:
        spec = KernelResourceSpec(
            allocations={DeviceName("cuda"): {GPU: {DeviceId(device_id): Decimal(1)}}},
            slots=ResourceSlot({GPU: Decimal(1)}),
            mounts=[],
            scratch_disk_size=0,
        )
        (config / "resource.txt").write_text(spec.write_to_string())
    if config_label:
        record = fake.containers[name]
        fake.containers[name] = dataclasses.replace(
            record, labels={**record.labels, CONFIG_DIR_LABEL: str(config)}
        )


def _held(context: ComputerContext, device_id: str) -> Decimal:
    return context.alloc_map.allocations[GPU][DeviceId(device_id)]


class TestRestoreContainerResources:
    @pytest.fixture
    def gpu(self, agent: ContainerdAgent) -> ComputerContext:
        context = _gpu_context()
        agent.computers = {DeviceName("cuda"): context}
        return context

    @pytest.fixture
    def scan_agent(
        self, agent: ContainerdAgent, monkeypatch: pytest.MonkeyPatch
    ) -> ContainerdAgent:
        agent.registry_lock = asyncio.Lock()
        monkeypatch.setattr(
            agent, "_load_kernel_registry_from_recovery", AsyncMock(return_value={})
        )
        monkeypatch.setattr(agent, "inject_container_lifecycle_event", AsyncMock())
        return agent

    async def test_scan_restores_from_resource_txt_not_the_plugin(
        self, scan_agent: ContainerdAgent, gpu: ComputerContext, tmp_path: Path
    ) -> None:
        _add_gpu_container(scan_agent, tmp_path, "c1", "0")

        await scan_agent.scan_running_kernels()

        assert _held(gpu, "0") == Decimal(1)
        cast(AsyncMock, gpu.instance.restore_from_container).assert_not_called()
        cast(AsyncMock, scan_agent.inject_container_lifecycle_event).assert_awaited_once()

    async def test_scan_continues_past_an_unreadable_resource_txt(
        self, scan_agent: ContainerdAgent, gpu: ComputerContext, tmp_path: Path
    ) -> None:
        _add_gpu_container(scan_agent, tmp_path, "c1", "0", resource_txt=False)
        _add_gpu_container(scan_agent, tmp_path, "c2", "1")

        await scan_agent.scan_running_kernels()

        assert _held(gpu, "0") == Decimal(0)
        assert _held(gpu, "1") == Decimal(1)
        assert cast(AsyncMock, scan_agent.inject_container_lifecycle_event).await_count == 2

    async def test_scan_skips_a_container_without_a_config_dir_label(
        self, scan_agent: ContainerdAgent, gpu: ComputerContext, tmp_path: Path
    ) -> None:
        _add_gpu_container(scan_agent, tmp_path, "c1", "0", config_label=False)
        _add_gpu_container(scan_agent, tmp_path, "c2", "1")

        await scan_agent.scan_running_kernels()

        assert _held(gpu, "0") == Decimal(0)
        assert _held(gpu, "1") == Decimal(1)

    async def test_scan_continues_past_a_corrupt_resource_txt(
        self, scan_agent: ContainerdAgent, gpu: ComputerContext, tmp_path: Path
    ) -> None:
        _add_gpu_container(scan_agent, tmp_path, "c1", "0")
        (tmp_path / "c1" / "resource.txt").write_text("not a resource spec")
        _add_gpu_container(scan_agent, tmp_path, "c2", "1")

        await scan_agent.scan_running_kernels()

        assert _held(gpu, "0") == Decimal(0)
        assert _held(gpu, "1") == Decimal(1)

    async def test_reconstruct_keeps_the_allocations_of_running_containers(
        self, agent: ContainerdAgent, gpu: ComputerContext, tmp_path: Path
    ) -> None:
        _add_gpu_container(agent, tmp_path, "c1", "0")
        _add_gpu_container(agent, tmp_path, "c2", "1")
        gpu.alloc_map.apply_allocation({GPU: {DeviceId("0"): Decimal(1)}})

        # The fixture replaces reconstruct_resource_usage with a mock; run the real one.
        await AbstractAgent.reconstruct_resource_usage(agent)

        assert _held(gpu, "0") == Decimal(1)
        assert _held(gpu, "1") == Decimal(1)
        cast(AsyncMock, gpu.instance.restore_from_container).assert_not_called()


class TestBaseRestoreContainerResources:
    @staticmethod
    def _plugin(error: Exception | None) -> ComputerContext:
        plugin = MagicMock(restore_from_container=AsyncMock(side_effect=error))
        return ComputerContext(instance=plugin, devices=[], alloc_map=MagicMock())

    def _container(self) -> Container:
        return Container(
            id=ContainerId("c1"),
            status=ContainerStatus.RUNNING,
            image="img:1",
            labels={},
            ports=[],
            backend_obj=None,
        )

    async def test_strict_tolerates_file_not_found_and_runs_the_next_plugin(
        self, agent: ContainerdAgent
    ) -> None:
        first, second = self._plugin(FileNotFoundError()), self._plugin(None)
        agent.computers = {DeviceName("a"): first, DeviceName("b"): second}

        await AbstractAgent._restore_container_resources(
            agent, KernelId(uuid.uuid4()), self._container()
        )

        cast(AsyncMock, second.instance.restore_from_container).assert_awaited_once()

    async def test_strict_propagates_other_errors(self, agent: ContainerdAgent) -> None:
        agent.computers = {DeviceName("a"): self._plugin(ValueError("bad"))}

        with pytest.raises(ValueError):
            await AbstractAgent._restore_container_resources(
                agent, KernelId(uuid.uuid4()), self._container()
            )

    async def test_lenient_tolerates_any_error_and_runs_the_next_plugin(
        self, agent: ContainerdAgent
    ) -> None:
        first, second = self._plugin(ValueError("bad")), self._plugin(None)
        agent.computers = {DeviceName("a"): first, DeviceName("b"): second}

        await AbstractAgent._restore_container_resources(
            agent, KernelId(uuid.uuid4()), self._container(), strict=False
        )

        cast(AsyncMock, second.instance.restore_from_container).assert_awaited_once()
