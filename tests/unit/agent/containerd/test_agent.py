from __future__ import annotations

import asyncio
import dataclasses
import pickle
import threading
import uuid
import weakref
from collections.abc import Mapping
from decimal import Decimal
from functools import partial
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.alloc_map import DiscretePropertyAllocMap
from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.agent.containerd import agent as agent_module
from ai.backend.agent.containerd.agent import (
    HOST_PORTS_LABEL,
    ContainerdAgent,
    _kernel_slots,
    _run_scratch_work,
)
from ai.backend.agent.containerd.client import ContainerRecord, TaskInfo, TaskState
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.profile.base import KernelLaunch, LaunchPlan, RuntimeProfile
from ai.backend.agent.containerd.profile.loader import select_profile
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    ContainerTaskStuck,
    KernelVerbNotSupported,
    ProfileNotApplicable,
)
from ai.backend.agent.errors.resources import InsufficientResource
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import ComputerContext, DeviceSlotInfo, KernelResourceSpec
from ai.backend.agent.types import (
    Container,
    ContainerLifecycleEvent,
    KernelOwnershipData,
    LifecycleEvent,
)
from ai.backend.common.events.kernel import KernelLifecycleEventReason
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
    Sentinel,
    SessionId,
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
    instance._stuck_kernels = {}
    instance._stuck_retry_task = None
    instance._resources_stale = False
    instance._tolerate_lookup_errors = False
    instance._lookup_warned = set()
    instance.restarting_kernels = {}
    instance.registry_lock = asyncio.Lock()
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


class _GpuAllocMap(DiscretePropertyAllocMap):
    @property
    def held(self) -> set[str]:
        return {str(dev) for dev, amount in self.allocations[SlotName("gpu")].items() if amount}


class _FakeKernel(dict[str, Any]):
    termination_reason: KernelLifecycleEventReason | None = None
    service_ports: list[Any] = []
    runner: None = None


class TestStuckKernel:
    """A kernel whose task is not confirmed gone keeps its device allocation reserved."""

    config_root: Path

    @pytest.fixture(autouse=True)
    def _config_root(self, tmp_path: Path) -> None:
        self.config_root = tmp_path / "config"

    @pytest.fixture
    def scratch_root(self, agent: ContainerdAgent, tmp_path: Path) -> Path:
        config = cast(MagicMock, agent.local_config)
        config.container.scratch_root = tmp_path
        config.debug.skip_container_deletion = False
        return tmp_path

    @pytest.fixture
    def clock(self, monkeypatch: pytest.MonkeyPatch) -> list[float]:
        now = [1000.0]
        monkeypatch.setattr(agent_module, "monotonic", lambda: now[0])
        return now

    @pytest.fixture
    def alloc_map(self, agent: ContainerdAgent, monkeypatch: pytest.MonkeyPatch) -> _GpuAllocMap:
        async def collect_logs(kernel_id: KernelId, container_id: str, iterator: Any) -> None:
            return None

        monkeypatch.setattr(agent, "collect_logs", collect_logs)
        monkeypatch.setattr(agent, "produce_error_event", AsyncMock())
        monkeypatch.setattr(
            agent,
            "reconstruct_resource_usage",
            partial(ContainerdAgent.reconstruct_resource_usage, agent),
        )
        alloc = _GpuAllocMap(
            device_slots={
                DeviceId("gpu0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("gpu"), Decimal(1))
            }
        )
        cast(Any, agent).computers = {
            DeviceName("gpu"): SimpleNamespace(alloc_map=alloc, instance=MagicMock())
        }
        return alloc

    def _add_gpu_container(self, agent: ContainerdAgent, state: TaskState | None) -> KernelId:
        fake = cast(FakeContainerd, agent._client)
        kid = _add_container(fake, "c1", state=state)
        record = fake.containers["c1"]
        config_dir = self.config_root / "c1"
        config_dir.mkdir(parents=True)
        spec = KernelResourceSpec(
            slots=ResourceSlot({"gpu": "1"}),
            allocations={DeviceName("gpu"): {SlotName("gpu"): {DeviceId("gpu0"): Decimal(1)}}},
            scratch_disk_size=0,
        )
        (config_dir / "resource.txt").write_text(spec.write_to_string())
        fake.containers["c1"] = dataclasses.replace(
            record, labels={**record.labels, CONFIG_DIR_LABEL: str(config_dir)}
        )
        for port in (30000, 30001):
            agent.port_pool.discard(port)
        return kid

    async def _stick(self, agent: ContainerdAgent, scratch_root: Path) -> KernelId:
        fake = cast(FakeContainerd, agent._client)
        kid = self._add_gpu_container(agent, TaskState.RUNNING)
        (scratch_root / str(kid)).mkdir()
        fake.failing.add("delete_task")
        await agent.clean_kernel(kid, ContainerId("c1"), False)
        return kid

    async def _init(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        base_scan: bool = False,
    ) -> None:
        """Start the agent as a restart would, with the base startup replaced.

        `base_scan` makes the replaced base startup enumerate the containers like the real one.
        """
        cast(MagicMock, agent.local_config).containerd = ContainerdConfig.model_validate({})

        async def scan() -> None:
            if base_scan:
                await agent.enumerate_containers(ContainerStatus.active_set())

        mocker.patch(
            "ai.backend.agent.agent.AbstractAgent.__ainit__", new=AsyncMock(side_effect=scan)
        )
        mocker.patch("ai.backend.agent.agent.AbstractAgent.shutdown", new=AsyncMock())
        await agent.__ainit__()

    async def test_clean_keeps_allocation_ports_and_scratch(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        kid = await self._stick(agent, scratch_root)

        await agent.reconstruct_resource_usage()

        assert agent._stuck_kernels["c1"].kernel_id == kid
        assert alloc_map.held == {"gpu0"}
        with pytest.raises(InsufficientResource):
            alloc_map.allocate({SlotName("gpu"): Decimal(1)})
        assert (scratch_root / str(kid)).exists()
        assert agent.port_pool.used_ports() == {30000, 30001}

    async def test_clean_of_a_stuck_launch_keeps_the_network_and_scratch(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        """A failed launch's clean event has no container id; the held task still needs both."""
        kid = await self._stick(agent, scratch_root)

        await agent.clean_kernel(kid, None, False)

        assert agent._stuck_kernels["c1"].kernel_id == kid
        assert (scratch_root / str(kid)).exists()
        assert agent.port_pool.used_ports() == {30000, 30001}

    async def test_hold_of_a_launch_keeps_its_ports_when_the_record_is_unreadable(
        self,
        agent: ContainerdAgent,
        clock: list[float],
    ) -> None:
        """A launch that failed early has no ports on the kernel yet and may have no record."""
        kid = KernelId(uuid.uuid4())
        agent.port_pool.discard(30004)

        await agent._hold_stuck(kid, "c-missing", [30004])

        assert agent._stuck_kernels["c-missing"].host_ports == [30004]

    async def test_the_clean_event_does_not_release_the_ports_of_a_stuck_kernel(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = self._add_gpu_container(agent, TaskState.RUNNING)
        fake.failing.add("delete_task")
        kernel_obj = MagicMock(runner=None, clean_event=None, close=AsyncMock())
        kernel_obj.get.return_value = [30000, 30001]
        agent.kernel_registry[kid] = kernel_obj
        agent._ongoing_destruction_tasks = weakref.WeakValueDictionary()
        agent.stat_ctx = MagicMock(remove_kernel_metric=AsyncMock())
        monkeypatch.setattr(agent, "anycast_and_broadcast_event", AsyncMock())
        event = ContainerLifecycleEvent(
            kid,
            SessionId(uuid.uuid4()),
            ContainerId("c1"),
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.SELF_TERMINATED,
        )

        await agent._handle_clean_event(event)

        assert kid not in agent.kernel_registry
        kernel_obj.__setitem__.assert_called_with("host_ports", [])
        assert agent.port_pool.used_ports() == {30000, 30001}
        assert alloc_map.held == {"gpu0"}

    async def test_a_cleaned_kernel_releases_its_allocation(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = self._add_gpu_container(agent, TaskState.RUNNING)

        await agent.clean_kernel(kid, ContainerId("c1"), False)
        await agent.reconstruct_resource_usage()

        assert agent._stuck_kernels == {}
        assert fake.containers == {}
        assert alloc_map.held == set()

    @pytest.mark.parametrize("failing_lookup", ["get_container", "get_task"])
    async def test_a_failing_lookup_is_stuck_and_releases_nothing(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
        failing_lookup: str,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = self._add_gpu_container(agent, TaskState.RUNNING)
        (scratch_root / str(kid)).mkdir()
        real_get_container = fake.get_container

        async def unreadable(container_id: str) -> None:
            raise ContainerdOperationFailed("injected failure")

        monkeypatch.setattr(fake, failing_lookup, unreadable)
        agent._orphan_ports[kid] = [30000, 30001]

        await agent.clean_kernel(kid, ContainerId("c1"), False)
        monkeypatch.setattr(fake, "get_container", real_get_container)
        await agent.reconstruct_resource_usage()
        assert "c1" in agent._stuck_kernels
        assert (scratch_root / str(kid)).exists()
        assert agent.port_pool.used_ports() == {30000, 30001}
        assert agent._stuck_kernels["c1"].host_ports == [30000, 30001]
        assert alloc_map.held == {"gpu0"}

    async def test_retry_success_runs_the_deferred_cleanup(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = await self._stick(agent, scratch_root)
        fake.failing.clear()
        clock[0] += 5.0

        await agent._retry_stuck_kernels()

        assert agent._stuck_kernels == {}
        assert fake.containers == {} and fake.tasks == {}
        assert alloc_map.held == set()
        assert alloc_map.allocate({SlotName("gpu"): Decimal(1)})
        assert not (scratch_root / str(kid)).exists()
        assert agent.port_pool.used_ports() == set()

    async def test_retry_waits_for_the_backoff_and_doubles_it_up_to_the_cap(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        await self._stick(agent, scratch_root)
        entry = agent._stuck_kernels["c1"]

        await agent._retry_stuck_kernels()
        assert entry.attempts == 0

        delays: list[float] = []
        for _ in range(8):
            clock[0] = entry.next_retry_at
            await agent._retry_stuck_kernels()
            delays.append(entry.next_retry_at - clock[0])
        await agent.reconstruct_resource_usage()

        assert delays == [10.0, 20.0, 40.0, 80.0, 160.0, 300.0, 300.0, 300.0]
        assert alloc_map.held == {"gpu0"}

    async def test_an_unexpected_error_backs_off_too(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await self._stick(agent, scratch_root)
        entry = agent._stuck_kernels["c1"]
        monkeypatch.setattr(agent_module, "clean_container", AsyncMock(side_effect=OSError))
        clock[0] = entry.next_retry_at

        await agent._retry_stuck_kernels()

        assert entry.next_retry_at == clock[0] + 10.0
        assert "c1" in agent._stuck_kernels

    async def test_error_event_once_after_thirty_minutes_and_allocation_stays_held(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        await self._stick(agent, scratch_root)
        entry = agent._stuck_kernels["c1"]
        produce = cast(AsyncMock, agent.produce_error_event)

        clock[0] += 29 * 60
        await agent._retry_stuck_kernels()
        produce.assert_not_awaited()

        clock[0] += 2 * 60
        await agent._retry_stuck_kernels()
        clock[0] = entry.next_retry_at
        await agent._retry_stuck_kernels()
        await agent.reconstruct_resource_usage()

        produce.assert_awaited_once()
        assert entry.attempts == 3
        assert alloc_map.held == {"gpu0"}

    async def test_sync_does_not_see_a_stuck_container(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        await self._stick(agent, scratch_root)

        found = await agent.enumerate_containers(
            ContainerStatus.active_set() | ContainerStatus.dead_set()
        )

        assert found == []

    async def test_restart_is_refused_before_it_starts(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        mocker: MockerFixture,
        kernel_config: KernelCreationConfig,
        ownership_data: KernelOwnershipData,
    ) -> None:
        await self._stick(agent, scratch_root)
        agent._stuck_kernels["c1"].kernel_id = ownership_data.kernel_id
        base = mocker.patch("ai.backend.agent.agent.AbstractAgent.restart_kernel", new=AsyncMock())

        with pytest.raises(ContainerTaskStuck, match="c1"):
            await agent.restart_kernel(ownership_data, MagicMock(), kernel_config)

        base.assert_not_awaited()
        assert ownership_data.kernel_id not in agent.restarting_kernels
        await agent.reconstruct_resource_usage()
        assert alloc_map.held == {"gpu0"}

    async def test_restart_whose_old_container_gets_stuck_fails_and_is_forgotten(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
        kernel_config: KernelCreationConfig,
        ownership_data: KernelOwnershipData,
    ) -> None:
        """The real base restart_kernel; its destroy handling and re-creation are faked."""
        kid = ownership_data.kernel_id
        fake = cast(FakeContainerd, agent._client)
        self._add_gpu_container(agent, TaskState.RUNNING)
        fake.containers["c1"] = dataclasses.replace(
            fake.containers["c1"],
            labels={**fake.containers["c1"].labels, "ai.backend.kernel-id": str(kid)},
        )
        fake.failing.add("delete_task")
        kernel_obj = _FakeKernel(
            container_id="c1",
            host_ports=[30000, 30001],
            repl_in_port=0,
            repl_out_port=0,
            stdin_port=0,
            stdout_port=0,
        )
        kernel_obj.termination_reason = KernelLifecycleEventReason.RESTARTING
        agent.kernel_registry[kid] = cast(Any, kernel_obj)
        queue: asyncio.Queue[ContainerLifecycleEvent | Sentinel] = asyncio.Queue()
        agent.container_lifecycle_queue = queue

        async def load_config(kernel_id: KernelId, name: str) -> bytes:
            return pickle.dumps({}) if name == "kconfig.dat" else b"{}"

        monkeypatch.setattr(agent, "restart_kernel__load_config", load_config)

        async def create_kernel(
            ownership: KernelOwnershipData,
            image: Any,
            config: Any,
            cluster_info: Any,
            *,
            restarting: bool,
        ) -> None:
            await agent.init_kernel_context(ownership, image, config, restarting=restarting)

        monkeypatch.setattr(agent, "create_kernel", create_kernel)

        async def destroy_handler() -> None:
            event = await queue.get()
            assert isinstance(event, ContainerLifecycleEvent)
            assert event.event == LifecycleEvent.DESTROY
            await agent.clean_kernel(kid, ContainerId("c1"), True)
            agent.restarting_kernels[kid].destroy_event.set()

        handler = asyncio.create_task(destroy_handler())
        with pytest.raises(ContainerTaskStuck):
            await agent.restart_kernel(ownership_data, MagicMock(), kernel_config)
        await handler

        assert kid not in agent.restarting_kernels
        event = queue.get_nowait()
        assert isinstance(event, ContainerLifecycleEvent)
        assert (event.event, event.reason) == (
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.FAILED_TO_START,
        )
        await agent.reconstruct_resource_usage()
        assert alloc_map.held == {"gpu0"}

    @pytest.mark.parametrize("restarting", [True, False])
    async def test_retry_success_keeps_the_scratch_only_while_the_kernel_restarts(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        restarting: bool,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = await self._stick(agent, scratch_root)
        if restarting:
            agent.restarting_kernels[kid] = MagicMock()
        fake.failing.clear()
        clock[0] += 5.0

        await agent._retry_stuck_kernels()

        assert (scratch_root / str(kid)).exists() is restarting

    async def test_retry_skips_an_entry_cleaned_meanwhile(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await self._stick(agent, scratch_root)
        entry = agent._stuck_kernels.pop("c1")
        clean = AsyncMock()
        monkeypatch.setattr(agent_module, "clean_container", clean)

        await agent._retry_stuck(entry)

        clean.assert_not_awaited()

    async def test_the_clean_runs_outside_the_registry_lock(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await self._stick(agent, scratch_root)
        locked: list[bool] = []

        async def clean(client: Any, container_id: str) -> None:
            locked.append(agent.registry_lock.locked())

        monkeypatch.setattr(agent_module, "clean_container", clean)
        clock[0] += 5.0

        await agent._retry_stuck_kernels()

        assert locked == [False]
        assert agent._stuck_kernels == {}

    async def test_a_failing_leftover_cleanup_is_not_a_failed_retry(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        await self._stick(agent, scratch_root)
        await agent.reconstruct_resource_usage()
        entry = agent._stuck_kernels["c1"]
        fake.failing.clear()
        monkeypatch.setattr(agent, "_remove_kernel_leftovers", AsyncMock(side_effect=OSError))
        info = mocker.patch.object(agent_module.log, "info")
        clock[0] += 5.0

        await agent._retry_stuck_kernels()

        assert not entry.escalated
        assert entry.next_retry_at == 1005.0
        assert alloc_map.held == set()
        assert info.call_args.args[0] == "stuck container cleaned"

    async def test_a_failing_error_event_does_not_stop_the_retry(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        await self._stick(agent, scratch_root)
        entry = agent._stuck_kernels["c1"]
        cast(AsyncMock, agent.produce_error_event).side_effect = ConnectionError
        clock[0] += 31 * 60

        await agent._retry_stuck_kernels()

        assert entry.escalated
        assert entry.next_retry_at > clock[0]

    async def test_the_retry_loop_survives_a_failing_cycle(
        self, agent: ContainerdAgent, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(agent_module, "_STUCK_RETRY_MIN_SEC", 0.0)
        cycle = AsyncMock(side_effect=[RuntimeError("boom"), None, None])
        monkeypatch.setattr(agent, "_retry_stuck_kernels", cycle)

        task = asyncio.create_task(agent._stuck_retry_loop())
        while cycle.await_count < 3:
            await asyncio.sleep(0)
        task.cancel()
        await asyncio.wait({task})

        assert task.cancelled()

    async def test_a_failed_rebuild_is_retried_on_the_next_cycle(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        await self._stick(agent, scratch_root)
        await agent.reconstruct_resource_usage()
        fake.failing.clear()
        clock[0] += 5.0
        real = agent.reconstruct_resource_usage
        monkeypatch.setattr(agent, "reconstruct_resource_usage", AsyncMock(side_effect=OSError))

        await agent._retry_stuck_kernels()

        stale_after_failure = agent._resources_stale
        assert agent._stuck_kernels == {}
        assert stale_after_failure
        assert alloc_map.held == {"gpu0"}

        monkeypatch.setattr(agent, "reconstruct_resource_usage", real)
        await agent._retry_stuck_kernels()

        assert not agent._resources_stale
        assert alloc_map.held == set()

    async def test_another_kernel_is_not_affected_by_a_stuck_container(
        self,
        agent: ContainerdAgent,
        scratch_root: Path,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        kernel_config: KernelCreationConfig,
        ownership_data: KernelOwnershipData,
    ) -> None:
        await self._stick(agent, scratch_root)
        agent._runtime_profiles = []

        ctx = await agent.init_kernel_context(
            ownership_data,
            MagicMock(),
            kernel_config,
            restarting=True,
        )

        assert ctx.kernel_id == ownership_data.kernel_id
        assert "c1" in agent._stuck_kernels

    @pytest.mark.parametrize("state", [TaskState.STOPPED, TaskState.UNKNOWN])
    async def test_restart_holds_and_retries_a_task_that_is_not_removed(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        state: TaskState,
    ) -> None:
        kid = self._add_gpu_container(agent, state)

        await self._init(agent, mocker, monkeypatch)
        try:
            assert agent._stuck_kernels["c1"].kernel_id == kid
            assert agent._stuck_kernels["c1"].host_ports == [30000, 30001]
            assert alloc_map.held == {"gpu0"}
            with pytest.raises(InsufficientResource):
                alloc_map.allocate({SlotName("gpu"): Decimal(1)})
            assert agent.port_pool.used_ports() == {30000, 30001}
            assert agent._stuck_retry_task is not None
        finally:
            await agent.shutdown(MagicMock())

    async def test_a_failed_lookup_in_a_sync_cycle_is_an_error_not_a_dead_container(
        self,
        agent: ContainerdAgent,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        self._add_gpu_container(agent, TaskState.RUNNING)

        async def unreadable(container_id: str) -> None:
            raise ContainerdOperationFailed("get_task: injected failure")

        monkeypatch.setattr(fake, "get_task", unreadable)

        with pytest.raises(ContainerdOperationFailed):
            await agent.enumerate_containers(
                ContainerStatus.active_set() | ContainerStatus.dead_set()
            )

    async def test_restart_survives_a_failing_task_lookup_and_keeps_the_allocation(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        self._add_gpu_container(agent, TaskState.RUNNING)

        async def unreadable(container_id: str) -> None:
            raise ContainerdOperationFailed("get_task: injected failure")

        monkeypatch.setattr(fake, "get_task", unreadable)

        await self._init(agent, mocker, monkeypatch, base_scan=True)
        try:
            assert "c1" in agent._stuck_kernels
            assert alloc_map.held == {"gpu0"}
            assert agent._tolerate_lookup_errors is False
        finally:
            await agent.shutdown(MagicMock())

    async def test_a_lookup_failure_is_warned_once_per_container_while_starting(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        self._add_gpu_container(agent, TaskState.RUNNING)

        async def unreadable(container_id: str) -> None:
            raise ContainerdOperationFailed("get_task: injected failure")

        monkeypatch.setattr(fake, "get_task", unreadable)
        agent._tolerate_lookup_errors = True
        warning = mocker.patch.object(agent_module.log, "warning")

        assert await agent.enumerate_containers() == []
        assert await agent.enumerate_containers() == []

        warning.assert_called_once()

    async def test_seeding_an_unreadable_task_keeps_the_allocation_and_schedules_a_retry(
        self,
        agent: ContainerdAgent,
        clock: list[float],
        alloc_map: _GpuAllocMap,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake = cast(FakeContainerd, agent._client)
        kid = self._add_gpu_container(agent, TaskState.RUNNING)

        async def unreadable(container_id: str) -> None:
            raise ContainerdOperationFailed("get_task: injected failure")

        monkeypatch.setattr(fake, "get_task", unreadable)

        await agent._seed_stuck_kernels()
        await agent.reconstruct_resource_usage()

        entry = agent._stuck_kernels["c1"]
        assert (entry.kernel_id, entry.next_retry_at) == (kid, clock[0] + 5.0)
        assert alloc_map.held == {"gpu0"}

    async def test_restart_holds_a_running_task_without_seeding_it(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        self._add_gpu_container(agent, TaskState.RUNNING)

        await self._init(agent, mocker, monkeypatch)
        try:
            assert agent._stuck_kernels == {}
            assert alloc_map.held == {"gpu0"}
        finally:
            await agent.shutdown(MagicMock())

    async def test_a_container_without_a_task_holds_nothing(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        self._add_gpu_container(agent, None)

        await self._init(agent, mocker, monkeypatch)
        try:
            assert agent._stuck_kernels == {}
            assert alloc_map.held == set()
        finally:
            await agent.shutdown(MagicMock())

    async def test_shutdown_cancels_the_retry_loop(
        self,
        agent: ContainerdAgent,
        mocker: MockerFixture,
        monkeypatch: pytest.MonkeyPatch,
        clock: list[float],
        alloc_map: _GpuAllocMap,
    ) -> None:
        await self._init(agent, mocker, monkeypatch)
        task = agent._stuck_retry_task
        assert task is not None and not task.done()

        await agent.shutdown(MagicMock())

        assert task.cancelled()


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


class TestRunScratchWork:
    async def test_cancellation_waits_for_the_thread_to_finish(self) -> None:
        """The scratch work is done before the cancel propagates, so a removal after it holds."""
        started = threading.Event()
        release = threading.Event()
        finished: list[bool] = []

        def work() -> None:
            started.set()
            release.wait(5)
            finished.append(True)

        task = asyncio.create_task(_run_scratch_work(work))
        await asyncio.get_running_loop().run_in_executor(None, started.wait, 5)

        task.cancel()
        await asyncio.sleep(0.05)
        assert not task.done()
        release.set()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished == [True]
