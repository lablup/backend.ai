from __future__ import annotations

import asyncio
import dataclasses
import uuid
from collections.abc import Sequence
from decimal import Decimal
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.containerd.agent import (
    HOST_PORTS_LABEL,
    KERNEL_IP_LABEL,
    ContainerdKernelCreationContext,
)
from ai.backend.agent.containerd.client import MountSpec
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.profile.base import LaunchPlan, RuntimeOptions
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.containerd.spec import SpecInput, build_base_spec, build_launch_spec
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    KernelNetworkSetupFailed,
    KernelVerbNotSupported,
    ProfileSpecRejected,
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
    ServicePortProtocols,
    SlotName,
)

from .conftest import FakeProfile
from .fakes import FakeCommandRunner, FakeContainerd

SLOTS = {SlotName("cpu"): Decimal(1), SlotName("mem"): Decimal(1024)}
PORT_RANGE = (30000, 30009)
BRIDGE = "bai-t"


def _local_config(scratch_root: Path) -> MagicMock:
    config = MagicMock()
    config.container.scratch_root = scratch_root
    config.container.kernel_uid = 1000
    config.container.kernel_gid = 1000
    config.container.advertised_host = None
    config.container.bind_host = "127.0.0.1"
    config.container.sandbox_type = "docker"
    config.debug.coredump.enabled = False
    return config


def _make_context(
    ownership_data: KernelOwnershipData,
    kernel_config: KernelCreationConfig,
    profile: FakeProfile,
    *,
    scratch_root: Path,
    client: FakeContainerd | None = None,
    port_pool: PortPool | None = None,
    computers: dict[DeviceName, ComputerContext] | None = None,
    runner: FakeCommandRunner | None = None,
    network: KernelNetwork | None = None,
) -> ContainerdKernelCreationContext:
    return ContainerdKernelCreationContext(
        ownership_data,
        MagicMock(),
        MagicMock(),
        kernel_config,
        "ubuntu22.04",
        _local_config(scratch_root),
        computers or {},
        profile=profile,
        slots=SLOTS,
        client=client or FakeContainerd(),
        port_pool=port_pool or PortPool(PORT_RANGE, cooldown_sec=0),
        network=network
        or KernelNetwork(
            BRIDGE,
            IPv4Network("172.30.9.0/24"),
            "10.0.0.5",
            PORT_RANGE,
            run=runner or FakeCommandRunner(),
        ),
        resource_lock=asyncio.Lock(),
    )


def _plugin() -> ComputerContext:
    plugin = MagicMock()
    plugin.generate_resource_data = AsyncMock(return_value={})
    return ComputerContext(instance=plugin, devices=[], alloc_map=MagicMock())


@pytest.fixture
def computers() -> dict[DeviceName, ComputerContext]:
    return {DeviceName("cpu"): _plugin(), DeviceName("mem"): _plugin()}


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
def launch_kernel_config(kernel_config: KernelCreationConfig) -> KernelCreationConfig:
    return cast(
        KernelCreationConfig,
        {**kernel_config, "cluster_hostname": "main1", "resource_opts": {"shmem": "134217728"}},
    )


class TestPrepareContainer:
    async def test_plan_is_called_once_with_the_launch(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        profile = FakeProfile("runc", accepts=True, plan_result=launch_plan)
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
        )
        await ctx.prepare_scratch()

        kernel = await ctx.prepare_container(resource_spec, {"A": "1"}, [], MagicMock())

        assert isinstance(kernel, ContainerdKernel)
        assert kernel.launch_plan is launch_plan
        assert len(profile.plan_calls) == 1
        launch = profile.plan_calls[0]
        assert launch.kernel_id == ownership_data.kernel_id
        assert launch.session_id == ownership_data.session_id
        assert launch.config is launch_kernel_config
        assert launch.slots is SLOTS
        assert launch.devices == ()
        assert launch.base_spec["linux"]["resources"]["cpu"]["cpus"] == "1,3"
        assert launch.base_spec["linux"]["resources"]["memory"]["limit"] == 1073741824
        assert launch.base_spec["hostname"] == "main1"
        assert launch.base_spec["linux"]["namespaces"][4] == {
            "type": "network",
            "path": f"/run/netns/{BRIDGE}-{ownership_data.kernel_id}",
        }

    async def test_config_files_are_written_for_the_kernel_runner(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        profile = FakeProfile("runc", accepts=True, plan_result=launch_plan)
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
        )
        await ctx.prepare_scratch()

        await ctx.prepare_container(resource_spec, {"A": "1", "B": "2"}, [], MagicMock())

        config_dir = tmp_path / str(ownership_data.kernel_id) / "config"
        assert (config_dir / "environ.txt").read_text() == "A=1\nB=2\n"
        assert "CPU_SHARES=1:1,3:1" in (config_dir / "resource.txt").read_text()

    async def test_profile_rejection_propagates(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        profile = FakeProfile("coco-tdx", accepts=True, plan_error=ProfileSpecRejected("bad"))
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
        )
        await ctx.prepare_scratch()

        with pytest.raises(ProfileSpecRejected):
            await ctx.prepare_container(resource_spec, {}, [], MagicMock())

    async def test_netns_exists_before_plan_and_is_removed_when_plan_fails(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        runner = FakeCommandRunner()
        profile = FakeProfile("coco-tdx", accepts=True, plan_error=ProfileSpecRejected("bad"))
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
            runner=runner,
        )
        await ctx.prepare_scratch()

        with pytest.raises(ProfileSpecRejected):
            await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        ns = f"{BRIDGE}-{ownership_data.kernel_id}"
        assert runner.calls[0] == ("ip", "netns", "add", ns)
        assert len(profile.plan_calls) == 1
        assert runner.matching("ip", "link", "show")  # the teardown ran

    async def test_setup_failing_part_way_removes_the_netns_and_frees_the_address(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        runner = FakeCommandRunner()
        ns = f"{BRIDGE}-{ownership_data.kernel_id}"
        runner.script(["ip", "netns", "list"], f"{ns}\n")
        runner.failing.add(("ip", "link", "set"))
        network = KernelNetwork(
            BRIDGE, IPv4Network("172.30.9.0/24"), "10.0.0.5", PORT_RANGE, run=runner
        )
        profile = FakeProfile("runc", accepts=True)
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
            network=network,
        )
        await ctx.prepare_scratch()

        with pytest.raises(KernelNetworkSetupFailed):
            await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        assert ("ip", "netns", "del", ns) in runner.calls
        assert profile.plan_calls == []
        runner.failing.clear()
        assert await network.setup(KernelId(uuid.uuid4())) == IPv4Address("172.30.9.2")


SPEC_JWS_ENTRY = {
    "destination": "/run/bai/spec.jws",
    "type": "bind",
    "options": ["rbind", "ro", "rprivate"],
}


class TestSealedKernel:
    @pytest.fixture
    def sealed_config(self, launch_kernel_config: KernelCreationConfig) -> KernelCreationConfig:
        return cast(
            KernelCreationConfig,
            {**launch_kernel_config, "confidential": {"signature": "aaa.bbb.ccc"}},
        )

    async def _prepare(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        *,
        runner: FakeCommandRunner | None = None,
        client: FakeContainerd | None = None,
    ) -> tuple[ContainerdKernelCreationContext, FakeProfile]:
        profile = FakeProfile("runc", accepts=True, plan_result=launch_plan)
        ctx = _make_context(
            ownership_data,
            config,
            profile,
            scratch_root=tmp_path,
            computers=computers,
            runner=runner,
            client=client,
        )
        await ctx.prepare_scratch()
        await ctx.prepare_container(resource_spec, {}, [], MagicMock())
        return ctx, profile

    async def test_signature_is_written_and_mounted_read_only(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        sealed_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        _, profile = await self._prepare(
            tmp_path, ownership_data, sealed_config, launch_plan, resource_spec, computers
        )

        path = (tmp_path / str(ownership_data.kernel_id)).resolve() / "spec.jws"
        assert path.read_bytes() == b"aaa.bbb.ccc"
        assert path.stat().st_mode & 0o777 == 0o444
        base_spec = profile.plan_calls[0].base_spec
        assert base_spec["mounts"][-1] == {**SPEC_JWS_ENTRY, "source": str(path)}

    async def test_the_mount_survives_into_the_runc_launch_spec(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        sealed_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        ctx, profile = await self._prepare(
            tmp_path, ownership_data, sealed_config, launch_plan, resource_spec, computers
        )
        launch = profile.plan_calls[0]
        plan = RuncProfile(10.0).plan(launch)

        spec = build_launch_spec(
            launch.base_spec,
            args=[],
            env=[],
            mounts=launch.mounts,
            allowed_mount_kinds=plan.allowed_mount_kinds,
            spec_patch=plan.spec_patch,
            cgroups_path="/ns/c",
        )

        path = (tmp_path / str(ownership_data.kernel_id)).resolve() / "spec.jws"
        entries = [m for m in spec["mounts"] if m["destination"] == "/run/bai/spec.jws"]
        assert entries == [{**SPEC_JWS_ENTRY, "source": str(path)}]

    async def test_unsealed_kernel_has_no_file_and_an_unchanged_base_spec(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        _, profile = await self._prepare(
            tmp_path, ownership_data, launch_kernel_config, launch_plan, resource_spec, computers
        )

        expected = build_base_spec(
            SpecInput(
                cwd="/home/work",
                hostname="main1",
                cpu_cores=[1, 3],
                memory_bytes=1073741824,
                shm_bytes=134217728,
                netns_path=f"/run/netns/{BRIDGE}-{ownership_data.kernel_id}",
            )
        )
        assert profile.plan_calls[0].base_spec == expected
        assert all(m["destination"] != "/run/bai/spec.jws" for m in expected["mounts"])
        assert not (tmp_path / str(ownership_data.kernel_id) / "spec.jws").exists()

    async def test_sealed_without_a_signature_fails_before_any_side_effect(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        config = cast(KernelCreationConfig, {**launch_kernel_config, "confidential": {}})
        runner = FakeCommandRunner()
        client = FakeContainerd()

        with pytest.raises(SealedSpecMissing):
            await self._prepare(
                tmp_path,
                ownership_data,
                config,
                launch_plan,
                resource_spec,
                computers,
                runner=runner,
                client=client,
            )

        assert runner.calls == []
        assert client.calls == []
        scratch = tmp_path / str(ownership_data.kernel_id)
        assert not (scratch / "spec.jws").exists()
        assert not (scratch / "config" / "environ.txt").exists()


class TestCreationContextMembers:
    def test_repl_ports_and_protected_services_stay_unsupported(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(
            ownership_data, kernel_config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

        with pytest.raises(KernelVerbNotSupported, match="repl_ports"):
            _ = ctx.repl_ports
        with pytest.raises(KernelVerbNotSupported, match="protected_services"):
            _ = ctx.protected_services

    async def test_extra_envs_are_empty(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(
            ownership_data, kernel_config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

        assert await ctx.get_extra_envs() == {}

    async def test_resource_spec_requires_cpu(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        config = cast(KernelCreationConfig, {**kernel_config, "resource_slots": {"mem": "1"}})
        ctx = _make_context(
            ownership_data, config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

        with pytest.raises(UnsupportedResource):
            await ctx.prepare_resource_spec()

    async def test_apply_network_is_a_noop(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(
            ownership_data, kernel_config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

        await ctx.apply_network(MagicMock())


class TestIntrinsicMounts:
    async def test_config_is_read_only_and_work_is_writable(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(
            ownership_data, kernel_config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

        mounts = {str(m.target): m for m in await ctx.get_intrinsic_mounts()}

        scratch = (tmp_path / str(ownership_data.kernel_id)).resolve()
        assert mounts["/home/config"].source == scratch / "config"
        assert mounts["/home/config"].permission.value == "ro"
        assert mounts["/home/work"].source == scratch / "work"
        assert mounts["/home/work"].permission.value == "rw"


class TestAccelerators:
    @pytest.fixture
    def ctx(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> ContainerdKernelCreationContext:
        return _make_context(
            ownership_data, kernel_config, FakeProfile("runc", accepts=True), scratch_root=tmp_path
        )

    @pytest.mark.parametrize("slot", ["cpu", "mem"])
    async def test_intrinsic_slots_are_accepted(
        self, ctx: ContainerdKernelCreationContext, slot: str
    ) -> None:
        alloc = {SlotName(slot): {DeviceId("root"): Decimal(1)}}

        await ctx.apply_accelerator_allocation(MagicMock(), alloc)
        assert await ctx.generate_accelerator_mounts(MagicMock(), alloc) == []

    async def test_allocated_accelerator_is_refused(
        self, ctx: ContainerdKernelCreationContext
    ) -> None:
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal("0.5")}}

        with pytest.raises(KernelVerbNotSupported, match=r"cuda\.shares"):
            await ctx.apply_accelerator_allocation(MagicMock(), alloc)
        with pytest.raises(KernelVerbNotSupported, match=r"cuda\.shares"):
            await ctx.generate_accelerator_mounts(MagicMock(), alloc)

    async def test_zero_accelerator_allocation_is_accepted(
        self, ctx: ContainerdKernelCreationContext
    ) -> None:
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(0)}}

        await ctx.apply_accelerator_allocation(MagicMock(), alloc)


class StdioRecordingContainerd(FakeContainerd):
    stdio: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.stdio = []

    @override
    async def create_task(
        self, container_id: str, rootfs: Sequence[MountSpec], stdout: str, stderr: str
    ) -> int:
        self.stdio.extend([stdout, stderr])
        return await super().create_task(container_id, rootfs, stdout, stderr)


class TestStartContainer:
    image_ref = "cr.example.com/stable/python:3.11"

    @pytest.fixture
    def fake(self) -> FakeContainerd:
        fake = FakeContainerd()
        fake.add_image(self.image_ref, diff_ids=["sha256:aa"], env=["PATH=/usr/bin", "LANG=C"])
        return fake

    async def _prepared(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        client: FakeContainerd,
        port_pool: PortPool,
        runner: FakeCommandRunner | None = None,
        service_ports: list[ServicePort] | None = None,
    ) -> tuple[ContainerdKernelCreationContext, ContainerdKernel]:
        profile = FakeProfile("runc", accepts=True, plan_result=launch_plan)
        ctx = _make_context(
            ownership_data,
            kernel_config,
            profile,
            scratch_root=tmp_path,
            client=client,
            port_pool=port_pool,
            computers=computers,
            runner=runner,
        )
        await ctx.prepare_scratch()
        resource_spec.mounts.extend(await ctx.get_intrinsic_mounts())
        await ctx.process_mounts(resource_spec.mounts)
        kernel = await ctx.prepare_container(
            resource_spec,
            {"LANG": "en_US.UTF-8", "LOCAL_USER_ID": "1000"},
            service_ports or [],
            MagicMock(),
        )
        return ctx, kernel

    async def test_container_is_created_and_started(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        data = await ctx.start_container(kernel, ["python", "-m", "kernel"], None, [], MagicMock())

        container_id = data["container_id"]
        assert container_id.startswith(str(ownership_data.kernel_id) + "-")
        assert fake.tasks[container_id].state.value == "running"
        assert fake.snapshots[container_id][0].options == ("lowerdir=sha256:aa",)
        spec: dict[str, Any] = dict(fake.specs[container_id])
        assert spec["process"]["args"] == ["/opt/kernel/entrypoint.sh", "python", "-m", "kernel"]
        assert spec["process"]["env"] == [
            "PATH=/usr/bin",
            "LANG=en_US.UTF-8",
            "LOCAL_USER_ID=1000",
        ]
        destinations = [m["destination"] for m in spec["mounts"] if m["type"] == "bind"]
        assert {"/home/config", "/home/work"} <= set(destinations)
        assert [ns["type"] for ns in spec["linux"]["namespaces"]] == [
            "pid",
            "ipc",
            "uts",
            "mount",
            "network",
            "cgroup",
        ]
        assert spec["linux"]["namespaces"][4]["path"] == (
            f"/run/netns/{BRIDGE}-{ownership_data.kernel_id}"
        )

    async def test_plan_runtime_options_reach_the_container(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        options = RuntimeOptions(type_url="runtimeoptions.v1.Options", value=b"\x12\x03abc")
        plan = dataclasses.replace(launch_plan, runtime_options=options)
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert fake.runtime_options[data["container_id"]] == options

    async def test_labels_identify_the_kernel_and_its_owner(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        labels = fake.containers[data["container_id"]].labels
        assert labels["ai.backend.kernel-id"] == str(ownership_data.kernel_id)
        assert labels["ai.backend.session-id"] == str(ownership_data.session_id)
        assert labels["ai.backend.owner"] == str(ownership_data.agent_id)
        assert labels[HOST_PORTS_LABEL] == ",".join(map(str, data["host_ports"]))
        assert labels[KERNEL_IP_LABEL] == data["kernel_ip"] == "172.30.9.2"
        assert labels[CONFIG_DIR_LABEL] == str(
            (tmp_path / str(ownership_data.kernel_id)).resolve() / "config"
        )

    async def test_cgroup_path_is_namespaced_by_container_id(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        spec = fake.specs[data["container_id"]]
        assert spec["linux"]["cgroupsPath"] == f"/{fake.namespace}/{data['container_id']}"

    async def test_service_ports_are_published_and_the_repl_is_not(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        runner = FakeCommandRunner(fake.calls)
        sports: list[ServicePort] = [
            {
                "name": "sshd",
                "protocol": ServicePortProtocols.TCP,
                "container_ports": (2200,),
                "host_ports": (None,),
                "is_inference": False,
            },
            {
                "name": "app",
                "protocol": ServicePortProtocols.HTTP,
                "container_ports": (8080, 8081),
                "host_ports": (None, None),
                "is_inference": False,
            },
        ]
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
            runner,
            sports,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        host_ports = data["host_ports"]
        assert len(set(host_ports)) == 3
        assert all(PORT_RANGE[0] <= p <= PORT_RANGE[1] for p in host_ports)
        assert [p for sport in sports for p in sport["host_ports"]] == host_ports
        assert (data["repl_in_port"], data["repl_out_port"]) == (0, 0)
        assert (data["stdin_port"], data["stdout_port"]) == (0, 0)
        assert data["kernel_host"] == "127.0.0.1"
        assert data["kernel_ip"] == "172.30.9.2"
        assert data["published_host"] == "10.0.0.5"
        assert "intrinsic_ports" not in data
        assert not (
            tmp_path / str(ownership_data.kernel_id) / "config" / "intrinsic-ports.json"
        ).exists()
        dnat = [c for c in runner.calls if "--to-destination" in c]
        assert [c[c.index("--to-destination") + 1] for c in dnat] == [
            "172.30.9.2:2200",
            "172.30.9.2:8080",
            "172.30.9.2:8081",
        ]
        assert len(pool) == 10 - 3

    async def test_network_is_set_up_before_the_task_is_created(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        runner = FakeCommandRunner(fake.calls)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
            runner,
        )

        await ctx.start_container(kernel, [], None, [], MagicMock())

        ops = [op for op, _ in fake.calls]
        assert ops.index("cmd") < ops.index("create_task")
        assert "ip -n bai-t-" in " ".join(key for op, key in fake.calls if op == "cmd")

    async def test_pool_exhaustion_releases_the_partial_ports(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool((30000, 30001), cooldown_sec=0)
        sport: ServicePort = {
            "name": "many",
            "protocol": ServicePortProtocols.TCP,
            "container_ports": (1, 2, 3),
            "host_ports": (None, None, None),
            "is_inference": False,
        }
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
            None,
            [sport],
        )

        with pytest.raises(PortPoolExhaustedError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(pool) == 2

    async def test_task_stdio_goes_to_the_scratch_log_file(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        fake = StdioRecordingContainerd()
        fake.add_image(self.image_ref, diff_ids=["sha256:aa"])
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        await ctx.start_container(kernel, [], None, [], MagicMock())

        expected = f"file://{(tmp_path / str(ownership_data.kernel_id)).resolve()}/task.log"
        assert fake.stdio == [expected, expected]

    async def test_each_launch_attempt_gets_a_fresh_container_id(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
        )

        first = await ctx.start_container(kernel, [], None, [], MagicMock())
        second = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert first["container_id"] != second["container_id"]

    async def test_missing_image_releases_ports_and_allocations(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        empty = FakeContainerd()
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        runner = FakeCommandRunner()
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            empty,
            pool,
            runner,
        )

        with pytest.raises(ContainerdImageNotFound):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(pool) == 10
        assert runner.matching("ip", "link", "show")  # the network teardown ran
        assert empty.containers == {}
        cast(MagicMock, computers[DeviceName("cpu")].alloc_map).free.assert_called_once()
        cast(MagicMock, computers[DeviceName("mem")].alloc_map).free.assert_called_once()

    async def test_launch_failure_releases_ports_and_leaves_no_container(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        launch_plan: LaunchPlan,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        fake.failing.add("start_task")
        pool = PortPool(PORT_RANGE, cooldown_sec=0)
        runner = FakeCommandRunner()
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            fake,
            pool,
            runner,
        )

        with pytest.raises(ContainerdOperationFailed, match="start_task"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(pool) == 10
        assert fake.containers == {}
        assert fake.snapshots == {}
        assert runner.matching("ip", "link", "show")  # the network teardown ran
