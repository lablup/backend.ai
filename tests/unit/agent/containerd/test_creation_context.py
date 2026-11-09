from __future__ import annotations

import asyncio
from decimal import Decimal
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import KERNEL_IP_LABEL
from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext as Ctx
from ai.backend.agent.containerd.intrinsic import CPUSET_LABEL, MEMORY_LABEL
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.profile.base import LaunchPlan, RuntimeProfile, TlsConnectReadiness
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.rpc.types import RuntimeOptions
from ai.backend.agent.errors.agent import ContainerCreationFailedError
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    KernelNetworkSetupFailed,
    SealedSpecMissing,
)
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import (
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    ServicePort,
    SlotName,
)

from .fakes import FakeCommandRunner, FakeContainerd

IMAGE = "cr.example.com/stable/python:3.11"


@pytest.fixture
def fake() -> FakeContainerd:
    fake = FakeContainerd()
    fake.add_image(
        IMAGE,
        diff_ids=["sha256:aa"],
        env=["PATH=/usr/bin", "LANG=C"],
        runtime={"Entrypoint": ["/bin/sh", "-c"], "Cmd": ["sleep 1"], "WorkingDir": "/srv"},
    )
    return fake


@pytest.fixture
def alloc_map() -> MagicMock:
    return MagicMock()


@pytest.fixture
def resource_spec() -> KernelResourceSpec:
    return KernelResourceSpec(
        slots=ResourceSlot({"cpu": "2", "mem": "1073741824"}),
        allocations={
            DeviceName("cpu"): {
                SlotName("cpu"): {DeviceId("1"): Decimal(1), DeviceId("3"): Decimal(1)}
            },
            DeviceName("mem"): {SlotName("mem"): {DeviceId("root"): Decimal(1073741824)}},
        },
        scratch_disk_size=0,
    )


@pytest.fixture
def port_pool() -> PortPool:
    return PortPool((30000, 30009), cooldown_sec=0)


@pytest.fixture
def ctx(
    ownership_data: KernelOwnershipData,
    fake: FakeContainerd,
    alloc_map: MagicMock,
    network: KernelNetwork,
    port_pool: PortPool,
    tmp_path: Path,
) -> Ctx:
    local_config = MagicMock()
    local_config.container.scratch_root = tmp_path
    local_config.container.sandbox_type = "docker"
    local_config.container.advertised_host = None
    local_config.container.bind_host = "10.0.0.5"
    computers = {
        DeviceName("cpu"): ComputerContext(MagicMock(), [], alloc_map),
        DeviceName("mem"): ComputerContext(MagicMock(), [], MagicMock()),
    }
    config = cast(
        KernelCreationConfig,
        {
            "image": {"canonical": IMAGE, "labels": {}},
            "resource_slots": {"cpu": "1", "mem": "1073741824"},
            "resource_opts": {"shmem": "134217728"},
            "uid": None,
            "main_gid": None,
            "supplementary_gids": [],
            "internal_data": None,
            "network_id": "net-1",
            "environ": {},
            "mounts": [],
            "cluster_hostname": "main1",
        },
    )
    return Ctx(
        ownership_data,
        MagicMock(),
        MagicMock(),
        config,
        "ubuntu22.04",
        local_config,
        computers,
        profile=RuncProfile(),
        client=fake,
        port_pool=port_pool,
        network=network,
        resource_lock=asyncio.Lock(),
    )


async def _prepare(
    ctx: Ctx,
    resource_spec: KernelResourceSpec,
    service_ports: list[ServicePort] | None = None,
) -> ContainerdKernel:
    return await ctx.prepare_container(
        resource_spec,
        {"LANG": "en_US.UTF-8", "LOCAL_USER_ID": "1000"},
        service_ports or [],
        MagicMock(),
    )


class TestPrepareContainer:
    async def test_network_is_set_up_and_joined_by_the_spec(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, runner: FakeCommandRunner
    ) -> None:
        await _prepare(ctx, resource_spec)

        ns = f"bai0-{ctx.kernel_id}"
        assert runner.matching("ip", "netns", "add") == [("ip", "netns", "add", ns)]
        assert ctx._base_spec["linux"]["namespaces"][4] == {
            "type": "network",
            "path": f"/run/netns/{ns}",
        }
        assert ctx._container_labels(resource_spec, [])[KERNEL_IP_LABEL] == "172.30.0.2"

    @pytest.mark.parametrize("error", [KernelNetworkSetupFailed("x"), asyncio.CancelledError()])
    async def test_interrupted_network_setup_is_torn_down(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        runner: FakeCommandRunner,
        monkeypatch: pytest.MonkeyPatch,
        error: BaseException,
    ) -> None:
        ns = f"bai0-{ctx.kernel_id}"
        runner.script(["ip", "netns", "list"], f"{ns}\n")

        async def interrupted(kernel_id: KernelId) -> IPv4Address:
            raise error

        monkeypatch.setattr(ctx._network, "setup", interrupted)

        with pytest.raises(type(error)):
            await _prepare(ctx, resource_spec)

        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", ns)]


class _PatchingProfile(RuntimeProfile):
    @property
    @override
    def name(self) -> str:
        return "patching"

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        options = RuntimeOptions(type_url="t/1", value=b"v")
        return LaunchPlan("io.example.v1", {"annotations": {"k": "v"}}, options)


class _TlsProfile(RuntimeProfile):
    PLAN = LaunchPlan("io.example.v1", readiness=TlsConnectReadiness("8080", 60.0))

    @property
    @override
    def name(self) -> str:
        return "tls"

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        return self.PLAN


class _FailingProfile(RuntimeProfile):
    @property
    @override
    def name(self) -> str:
        return "failing"

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        raise RuntimeError("plan failed")


def _sealed(config: KernelCreationConfig, signature: str) -> KernelCreationConfig:
    return cast(KernelCreationConfig, {**config, "confidential": {"signature": signature}})


def _rebuilt(ctx: Ctx, config: KernelCreationConfig, profile: RuntimeProfile | None = None) -> Ctx:
    return Ctx(
        ctx.ownership_data,
        MagicMock(),
        MagicMock(),
        config,
        "ubuntu22.04",
        ctx.local_config,
        ctx.computers,
        profile=profile or RuncProfile(),
        client=ctx._client,
        network=ctx._network,
        port_pool=ctx._port_pool,
        resource_lock=asyncio.Lock(),
    )


class _MountPatchingProfile(RuntimeProfile):
    @property
    @override
    def name(self) -> str:
        return "mount-patching"

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        return LaunchPlan("io.example.v1", {"mounts": []})


class _NamingProfile(RuntimeProfile):
    @property
    @override
    def name(self) -> str:
        return "naming"

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        return LaunchPlan("io.containerd.runc.v2")

    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        return "named reason"


class TestSealedSpec:
    async def test_unsealed_kernel_has_no_spec_mount(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, fake: FakeContainerd
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        mounts = dict(fake.specs[data["container_id"]][1])["mounts"]
        assert all(m["destination"] != "/run/bai/spec.jws" for m in mounts)

    async def test_sealed_kernel_gets_the_signature_file_and_mount(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, fake: FakeContainerd, tmp_path: Path
    ) -> None:
        sealed = _rebuilt(ctx, _sealed(ctx.kernel_config, "aaa.bbb.ccc"))
        kernel = await _prepare(sealed, resource_spec)

        data = await sealed.start_container(kernel, [], None, [], MagicMock())

        path = tmp_path / str(sealed.kernel_id) / "spec.jws"
        assert path.read_bytes() == b"aaa.bbb.ccc"
        assert dict(fake.specs[data["container_id"]][1])["mounts"][-1] == {
            "destination": "/run/bai/spec.jws",
            "type": "bind",
            "source": str(path),
            "options": ["rbind", "ro", "rprivate"],
        }

    async def test_profile_patching_mounts_keeps_the_spec_mount(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, fake: FakeContainerd
    ) -> None:
        sealed = _rebuilt(ctx, _sealed(ctx.kernel_config, "aaa.bbb.ccc"), _MountPatchingProfile())
        kernel = await _prepare(sealed, resource_spec)

        data = await sealed.start_container(kernel, [], None, [], MagicMock())

        mounts = dict(fake.specs[data["container_id"]][1])["mounts"]
        assert [m["destination"] for m in mounts] == ["/run/bai/spec.jws"]

    async def test_sealed_kernel_without_a_signature_is_refused_at_construction(
        self, ctx: Ctx
    ) -> None:
        config = cast(KernelCreationConfig, {**ctx.kernel_config, "confidential": {}})

        with pytest.raises(SealedSpecMissing):
            _rebuilt(ctx, config)

    async def test_failed_network_setup_removes_the_signature_file(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        runner: FakeCommandRunner,
        tmp_path: Path,
    ) -> None:
        sealed = _rebuilt(ctx, _sealed(ctx.kernel_config, "aaa.bbb.ccc"))
        runner.script(["ip", "netns", "add"], returncode=1)

        with pytest.raises(KernelNetworkSetupFailed):
            await _prepare(sealed, resource_spec)

        assert not (tmp_path / str(sealed.kernel_id)).exists()

    async def test_failed_launch_removes_the_signature_file(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, fake: FakeContainerd, tmp_path: Path
    ) -> None:
        sealed = _rebuilt(ctx, _sealed(ctx.kernel_config, "aaa.bbb.ccc"))
        kernel = await _prepare(sealed, resource_spec)
        fake.failing.add("create_task")

        with pytest.raises(ContainerdOperationFailed):
            await sealed.start_container(kernel, [], None, [], MagicMock())

        assert not (tmp_path / str(sealed.kernel_id)).exists()


class TestCreateFailureReason:
    async def test_profile_reason_is_added_to_the_creation_error(
        self, ctx: Ctx, resource_spec: KernelResourceSpec, fake: FakeContainerd
    ) -> None:
        ctx._profile = _NamingProfile()
        kernel = await _prepare(ctx, resource_spec)
        fake.failing.add("create_task")

        with pytest.raises(ContainerCreationFailedError, match="named reason: ") as exc_info:
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert isinstance(exc_info.value.__cause__, ContainerdOperationFailed)


class TestStartContainer:
    async def test_failing_profile_plan_frees_the_allocations_and_tears_the_network_down(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        alloc_map: MagicMock,
        port_pool: PortPool,
        runner: FakeCommandRunner,
    ) -> None:
        ns = f"bai0-{ctx.kernel_id}"
        sports = [cast(ServicePort, {"name": "web", "container_ports": (8080,)})]
        kernel = await _prepare(ctx, resource_spec, sports)
        runner.script(["ip", "netns", "list"], f"{ns}\n")
        ctx._profile = _FailingProfile()
        before = len(port_pool)

        with pytest.raises(RuntimeError, match="plan failed"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(port_pool) == before
        cast(MagicMock, alloc_map.free).assert_called_once()
        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", ns)]
        assert fake.containers == {} and fake.snapshots == {} and fake.tasks == {}

    async def test_container_uses_the_runtime_of_the_profile_plan(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
    ) -> None:
        ctx._profile = _PatchingProfile()
        kernel = await _prepare(ctx, resource_spec)

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        cid = data["container_id"]
        runtime, spec = fake.specs[cid]
        assert runtime == "io.example.v1"
        assert fake.runtime_options[cid] == RuntimeOptions(type_url="t/1", value=b"v")
        assert dict(spec)["annotations"] == {"k": "v"}

    async def test_container_runs_the_image_command_on_runc(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        ownership_data: KernelOwnershipData,
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        cid = data["container_id"]
        assert cid.startswith(f"{ownership_data.kernel_id}-")
        assert data == {
            "container_id": cid,
            "kernel_host": "10.0.0.5",
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
            "host_ports": [],
            "kernel_ip": "172.30.0.2",
            "published_host": "10.0.0.5",
        }
        runtime, raw_spec = fake.specs[cid]
        spec: dict[str, Any] = dict(raw_spec)
        assert runtime == "io.containerd.runc.v2"
        assert fake.tasks[cid].state.value == "running"
        assert spec["hostname"] == "main1"
        assert spec["linux"]["resources"]["cpu"]["cpus"] == "1,3"
        assert spec["process"]["args"] == ["/bin/sh", "-c", "sleep 1"]
        assert spec["process"]["cwd"] == "/srv"
        assert spec["process"]["env"] == ["PATH=/usr/bin", "LANG=en_US.UTF-8", "LOCAL_USER_ID=1000"]
        labels = fake.containers[cid].labels
        assert labels[CPUSET_LABEL] == "1,3"
        assert labels[MEMORY_LABEL] == "1073741824"
        assert labels["ai.backend.kernel-id"] == str(ownership_data.kernel_id)

    async def test_kernel_gets_the_launch_plan_of_the_profile(
        self, ctx: Ctx, resource_spec: KernelResourceSpec
    ) -> None:
        ctx._profile = _TlsProfile()
        kernel = await _prepare(ctx, resource_spec)
        assert kernel.launch_plan is None

        await ctx.start_container(kernel, [], None, [], MagicMock())

        assert kernel.launch_plan == _TlsProfile.PLAN

    async def test_service_ports_get_host_ports_and_dnat_rules(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        runner: FakeCommandRunner,
    ) -> None:
        sports = [
            cast(ServicePort, {"name": "web", "container_ports": (8080, 8081)}),
            cast(ServicePort, {"name": "ssh", "container_ports": (22,)}),
        ]
        kernel = await _prepare(ctx, resource_spec, sports)

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert data["host_ports"] == [30000, 30001, 30002]
        assert [tuple(s["host_ports"]) for s in sports] == [(30000, 30001), (30002,)]
        targets = [c[-1] for c in runner.matching("iptables", "-w", "-t", "nat", "-A", "bai0-DNAT")]
        assert targets == ["172.30.0.2:8080", "172.30.0.2:8081", "172.30.0.2:22"]
        labels = fake.containers[data["container_id"]].labels
        assert labels["ai.backend.containerd.host-ports"] == "30000,30001,30002"

    async def test_failed_launch_returns_the_host_ports(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        port_pool: PortPool,
    ) -> None:
        sports = [cast(ServicePort, {"name": "web", "container_ports": (8080,)})]
        kernel = await _prepare(ctx, resource_spec, sports)
        fake.failing.add("create_task")
        before = len(port_pool)

        with pytest.raises(ContainerdOperationFailed):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(port_pool) == before
        assert port_pool.acquire() == 30001

    async def test_start_before_prepare_raises(
        self, ctx: Ctx, resource_spec: KernelResourceSpec
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)
        ctx._address = None

        with pytest.raises(KernelNetworkSetupFailed, match="before prepare_container"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

    async def test_failed_launch_frees_the_allocations_and_leaves_nothing(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        alloc_map: MagicMock,
        runner: FakeCommandRunner,
    ) -> None:
        ns = f"bai0-{ctx.kernel_id}"
        kernel = await _prepare(ctx, resource_spec)
        runner.script(["ip", "netns", "list"], f"{ns}\n")
        fake.failing.add("create_task")

        with pytest.raises(ContainerdOperationFailed, match="create_task"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        cast(MagicMock, alloc_map.free).assert_called_once()
        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", ns)]
        assert fake.containers == {} and fake.snapshots == {} and fake.tasks == {}

    async def test_cancelled_launch_frees_the_allocations_and_leaves_nothing(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        alloc_map: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)
        create_task = fake.create_task

        async def created_then_cancelled(*args: Any, **kwargs: Any) -> Any:
            await create_task(*args, **kwargs)
            raise asyncio.CancelledError

        monkeypatch.setattr(fake, "create_task", created_then_cancelled)

        with pytest.raises(asyncio.CancelledError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        cast(MagicMock, alloc_map.free).assert_called_once()
        assert fake.containers == {} and fake.snapshots == {} and fake.tasks == {}

    async def test_pool_exhaustion_releases_the_ports_taken_and_frees_the_allocations(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        alloc_map: MagicMock,
        port_pool: PortPool,
    ) -> None:
        sports = [cast(ServicePort, {"name": "many", "container_ports": tuple(range(8000, 8011))})]
        kernel = await _prepare(ctx, resource_spec, sports)
        before = len(port_pool)

        with pytest.raises(PortPoolExhaustedError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(port_pool) == before
        cast(MagicMock, alloc_map.free).assert_called_once()

    async def test_cancelled_launch_returns_the_host_ports(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        port_pool: PortPool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sports = [cast(ServicePort, {"name": "web", "container_ports": (8080,)})]
        kernel = await _prepare(ctx, resource_spec, sports)
        before = len(port_pool)

        async def cancelled(*args: Any, **kwargs: Any) -> Any:
            raise asyncio.CancelledError

        monkeypatch.setattr(fake, "create_task", cancelled)

        with pytest.raises(asyncio.CancelledError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(port_pool) == before
