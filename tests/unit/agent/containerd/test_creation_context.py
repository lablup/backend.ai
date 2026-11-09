from __future__ import annotations

import asyncio
from decimal import Decimal
from ipaddress import IPv4Address
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import KERNEL_IP_LABEL
from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext as Ctx
from ai.backend.agent.containerd.intrinsic import CPUSET_LABEL, MEMORY_LABEL
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.errors.containerd import ContainerdOperationFailed, KernelNetworkSetupFailed
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
) -> Ctx:
    local_config = MagicMock()
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


class TestStartContainer:
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

        alloc_map.free.assert_called_once()
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
        alloc_map.free.assert_called_once()

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
