from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import stat as stat_mod
from collections.abc import Mapping, Sequence
from decimal import Decimal
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.containerd import agent as agent_module
from ai.backend.agent.containerd.agent import (
    HOST_PORTS_LABEL,
    ContainerdKernelCreationContext,
)
from ai.backend.agent.containerd.client import MountSpec
from ai.backend.agent.containerd.hostconfig import translate_fragment
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import (
    GeneratedMountKind,
    LaunchPlan,
    RuntimeOptions,
    TranslatedDevice,
)
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    HostConfigNotTranslatable,
    KernelVerbNotSupported,
    ProfileSpecRejected,
)
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import ComputerContext, KernelResourceSpec, Mount
from ai.backend.agent.types import KernelOwnershipData, MountInfo
from ai.backend.common.types import (
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    MountTypes,
    ResourceSlot,
    SlotName,
)

from .conftest import FakeProfile
from .fakes import FakeContainerd

SLOTS = {SlotName("cpu"): Decimal(1), SlotName("mem"): Decimal(1024)}
PORT_RANGE = (30000, 30009)


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
        resource_lock=asyncio.Lock(),
    )


def _accelerator_plugin(
    key: str, fragment: Mapping[str, Any], mounts: Sequence[MountInfo] = ()
) -> MagicMock:
    plugin = MagicMock(key=DeviceName(key))
    plugin.generate_docker_args = AsyncMock(return_value=fragment)
    plugin.generate_mounts = AsyncMock(return_value=list(mounts))
    return plugin


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

    async def test_network_is_a_noop_for_the_host_namespace(
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
    def fake(self) -> FakeContainerd:
        return FakeContainerd()

    @pytest.fixture
    def profile(self, launch_plan: LaunchPlan) -> FakeProfile:
        return FakeProfile("runc", accepts=True, plan_result=launch_plan)

    @pytest.fixture
    def ctx(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        computers: dict[DeviceName, ComputerContext],
        profile: FakeProfile,
        fake: FakeContainerd,
    ) -> ContainerdKernelCreationContext:
        return _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            client=fake,
            computers=computers,
        )

    @pytest.mark.parametrize("slot", ["cpu", "mem"])
    async def test_intrinsic_slots_are_accepted(
        self,
        ctx: ContainerdKernelCreationContext,
        profile: FakeProfile,
        fake: FakeContainerd,
        resource_spec: KernelResourceSpec,
        slot: str,
    ) -> None:
        alloc = {SlotName(slot): {DeviceId("root"): Decimal(1)}}
        await ctx.prepare_scratch()

        await ctx.apply_accelerator_allocation(_accelerator_plugin(slot, {}), alloc)
        await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        assert profile.plan_calls[0].devices == ()
        assert fake.calls == []

    async def test_zero_accelerator_allocation_is_accepted(
        self, ctx: ContainerdKernelCreationContext
    ) -> None:
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(0)}}

        await ctx.apply_accelerator_allocation(_accelerator_plugin("cuda", {}), alloc)

    async def test_accelerator_mounts_come_from_the_plugin(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
    ) -> None:
        await ctx.prepare_scratch()
        info = MountInfo(MountTypes.BIND, tmp_path / "acc-src", Path("/opt/accel"))
        plugin = _accelerator_plugin("cuda", {}, mounts=[info])
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(1)}}

        mounts = await ctx.generate_accelerator_mounts(plugin, alloc)

        source_dir = tmp_path / str(ownership_data.kernel_id) / "config" / "cuda"
        assert mounts == [info]
        plugin.generate_mounts.assert_awaited_once_with(source_dir, alloc)
        assert source_dir.is_dir()

    async def test_accelerator_mounts_are_tagged_accelerator(
        self,
        tmp_path: Path,
        ctx: ContainerdKernelCreationContext,
        profile: FakeProfile,
        resource_spec: KernelResourceSpec,
    ) -> None:
        await ctx.prepare_scratch()
        src = tmp_path / "acc-src"
        info = MountInfo(MountTypes.BIND, src, Path("/opt/accel"))
        plugin = _accelerator_plugin("cuda", {}, mounts=[info])
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(1)}}
        await ctx.generate_accelerator_mounts(plugin, alloc)

        await ctx.process_mounts([
            Mount(MountTypes.BIND, src, Path("/opt/accel")),
            Mount(MountTypes.BIND, tmp_path, Path("/mnt/vfolder")),
        ])
        await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        kinds = {m.target: m.kind for m in profile.plan_calls[0].mounts}
        assert kinds == {
            "/opt/accel": GeneratedMountKind.ACCELERATOR,
            "/mnt/vfolder": GeneratedMountKind.VFOLDER,
        }


class TestHostConfigTranslation:
    @pytest.fixture
    def fake(self) -> FakeContainerd:
        return FakeContainerd()

    @pytest.fixture
    def profile(self, launch_plan: LaunchPlan) -> FakeProfile:
        return FakeProfile("runc", accepts=True, plan_result=launch_plan)

    @pytest.fixture
    def ctx(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        computers: dict[DeviceName, ComputerContext],
        profile: FakeProfile,
        fake: FakeContainerd,
    ) -> ContainerdKernelCreationContext:
        return _make_context(
            ownership_data,
            launch_kernel_config,
            profile,
            scratch_root=tmp_path,
            client=fake,
            computers=computers,
        )

    @staticmethod
    async def _apply(
        ctx: ContainerdKernelCreationContext, key: str, fragment: Mapping[str, Any]
    ) -> None:
        alloc = {SlotName(f"{key}.shares"): {DeviceId("0"): Decimal(1)}}
        await ctx.apply_accelerator_allocation(_accelerator_plugin(key, fragment), alloc)

    async def test_device_reaches_the_launch_and_the_base_spec(
        self,
        ctx: ContainerdKernelCreationContext,
        profile: FakeProfile,
        fake: FakeContainerd,
        resource_spec: KernelResourceSpec,
    ) -> None:
        st = os.stat("/dev/null")
        major, minor = os.major(st.st_rdev), os.minor(st.st_rdev)
        await ctx.prepare_scratch()
        await self._apply(ctx, "cuda", {"HostConfig": {"Devices": [{"PathOnHost": "/dev/null"}]}})

        await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        (launch,) = profile.plan_calls
        assert launch.devices == (TranslatedDevice("/dev/null", "c", major, minor, "rwm"),)
        assert [d["path"] for d in launch.base_spec["linux"]["devices"]] == ["/dev/null"]
        assert launch.base_spec["linux"]["resources"]["devices"][-1] == {
            "allow": True,
            "type": "c",
            "major": major,
            "minor": minor,
            "access": "rwm",
        }
        assert fake.calls == []

    async def test_plugin_env_reaches_environ_and_the_kernel(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
        resource_spec: KernelResourceSpec,
    ) -> None:
        await ctx.prepare_scratch()
        await self._apply(ctx, "cuda", {"Env": ["X=plugin", "K=plugin"]})

        kernel = await ctx.prepare_container(
            resource_spec, {"K": "kernel", "A": "1"}, [], MagicMock()
        )

        config_dir = tmp_path / str(ownership_data.kernel_id) / "config"
        assert (config_dir / "environ.txt").read_text() == "K=plugin\nA=1\nX=plugin\n"
        assert kernel.environ["X"] == "plugin"
        assert kernel.environ["K"] == "plugin"

    async def test_confidential_plugin_with_no_docker_args_launches_without_devices(
        self,
        ctx: ContainerdKernelCreationContext,
        profile: FakeProfile,
        fake: FakeContainerd,
        resource_spec: KernelResourceSpec,
    ) -> None:
        alloc = {SlotName("confidential.tdx"): {DeviceId("0"): Decimal(1)}}
        await ctx.prepare_scratch()

        await ctx.apply_accelerator_allocation(_accelerator_plugin("confidential", {}), alloc)
        kernel = await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        assert isinstance(kernel, ContainerdKernel)
        assert profile.plan_calls[0].devices == ()
        assert fake.calls == []

    async def test_c5_vfio_fragment_reaches_the_launch_and_the_base_spec(
        self,
        monkeypatch: pytest.MonkeyPatch,
        ctx: ContainerdKernelCreationContext,
        profile: FakeProfile,
        resource_spec: KernelResourceSpec,
    ) -> None:
        node = cast(
            os.stat_result,
            SimpleNamespace(
                st_mode=stat_mod.S_IFCHR | 0o666, st_rdev=os.makedev(237, 0), st_uid=0, st_gid=0
            ),
        )
        monkeypatch.setattr(
            agent_module,
            "translate_fragment",
            partial(translate_fragment, stat=lambda _path: node),
        )
        fragment = {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": "/dev/vfio/devices/vfio0",
                        "PathInContainer": "/dev/vfio/devices/vfio0",
                        "CgroupPermissions": "rwm",
                    }
                ]
            }
        }
        alloc = {SlotName("cuda.device"): {DeviceId("0"): Decimal(1)}}
        await ctx.prepare_scratch()

        await ctx.apply_accelerator_allocation(_accelerator_plugin("cuda", fragment), alloc)
        await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        (launch,) = profile.plan_calls
        assert launch.devices == (TranslatedDevice("/dev/vfio/devices/vfio0", "c", 237, 0, "rwm"),)
        assert launch.base_spec["linux"]["resources"]["devices"] == [
            {"allow": False, "access": "rwm"},
            {"allow": True, "type": "c", "major": 237, "minor": 0, "access": "rwm"},
        ]

    @pytest.mark.parametrize(
        "host_config",
        [
            {"Sysctls": {"net.core.somaxconn": "1024"}},
            {"Sysctls": {}},
            {"Runtime": "nvidia"},
            {"SecurityOpt": ["seccomp=unconfined"]},
            {"GroupAdd": ["video"]},
            {"Mounts": [{"Type": "bind"}]},
            {"Privileged": True},
            {"Cpus": 2},
            {"Memory": 1},
            {"MemorySwap": 1},
            {"Ipc": "host"},
        ],
    )
    async def test_untranslatable_host_config_key_raises_before_any_containerd_call(
        self,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
        host_config: Mapping[str, Any],
    ) -> None:
        (key,) = host_config

        with pytest.raises(HostConfigNotTranslatable, match=rf"cuda: HostConfig\.{key}"):
            await self._apply(ctx, "cuda", {"HostConfig": host_config})

        assert fake.calls == []

    @pytest.mark.parametrize("fragment", [{"Cmd": ["x"]}, {"Labels": {}}, {"Devices": []}])
    async def test_unknown_top_level_key_raises_before_any_containerd_call(
        self,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
        fragment: Mapping[str, Any],
    ) -> None:
        (key,) = fragment

        with pytest.raises(HostConfigNotTranslatable, match=rf"cuda: {key}"):
            await self._apply(ctx, "cuda", fragment)

        assert fake.calls == []

    async def test_docker_cpu_fragment_from_a_cpu_plugin_raises(
        self, ctx: ContainerdKernelCreationContext, fake: FakeContainerd
    ) -> None:
        fragment = {"HostConfig": {"CpusetCpus": "0", "CpuQuota": 1}}

        with pytest.raises(HostConfigNotTranslatable, match=r"cpu: HostConfig\.CpusetCpus"):
            await self._apply(ctx, "cpu", fragment)

        assert fake.calls == []

    async def test_non_cdi_device_request_raises_before_any_containerd_call(
        self, ctx: ContainerdKernelCreationContext, fake: FakeContainerd
    ) -> None:
        fragment = {"HostConfig": {"DeviceRequests": [{"Driver": "nvidia", "Count": -1}]}}

        with pytest.raises(HostConfigNotTranslatable, match=r"cuda: HostConfig\.DeviceRequests"):
            await self._apply(ctx, "cuda", fragment)

        assert fake.calls == []

    async def test_untranslatable_fragment_removes_the_scratch(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
    ) -> None:
        scratch = tmp_path / str(ownership_data.kernel_id)
        await ctx.prepare_scratch()
        assert scratch.is_dir()

        with pytest.raises(HostConfigNotTranslatable):
            await self._apply(ctx, "cuda", {"HostConfig": {"Sysctls": {}}})

        assert not scratch.exists()
        assert fake.calls == []

    async def test_conflicting_plugins_raise_at_the_second_allocation(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
    ) -> None:
        await ctx.prepare_scratch()
        await self._apply(ctx, "cuda", {"Env": ["A=1"]})

        with pytest.raises(HostConfigNotTranslatable, match='"cuda" and "rocm"'):
            await self._apply(ctx, "rocm", {"Env": ["A=2"]})

        assert [name for name, _ in ctx._host_configs] == ["cuda"]
        assert ctx._host_config.env == (("A", "1"),)
        scratch = tmp_path / str(ownership_data.kernel_id)
        assert not scratch.exists()

    async def test_plugin_error_propagates_and_removes_the_scratch(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
    ) -> None:
        await ctx.prepare_scratch()
        scratch = tmp_path / str(ownership_data.kernel_id)
        assert scratch.is_dir()
        plugin = _accelerator_plugin("cuda", {})
        plugin.generate_docker_args = AsyncMock(side_effect=UnsupportedResource("cuda"))
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(1)}}

        with pytest.raises(UnsupportedResource):
            await ctx.apply_accelerator_allocation(plugin, alloc)

        assert not scratch.exists()
        assert fake.calls == []


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
        )
        await ctx.prepare_scratch()
        resource_spec.mounts.extend(await ctx.get_intrinsic_mounts())
        await ctx.process_mounts(resource_spec.mounts)
        kernel = await ctx.prepare_container(
            resource_spec, {"LANG": "en_US.UTF-8", "LOCAL_USER_ID": "1000"}, [], MagicMock()
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
        assert all(ns["type"] != "network" for ns in spec["linux"]["namespaces"])

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

    async def test_repl_ports_come_from_the_pool_and_reach_the_kernel_runner(
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

        ports = data["intrinsic_ports"]
        assert set(ports) == {"replin", "replout", "sshd", "ttyd"}
        assert len(set(ports.values())) == 4
        assert all(PORT_RANGE[0] <= p <= PORT_RANGE[1] for p in ports.values())
        assert data["host_ports"] == list(ports.values())
        assert (data["repl_in_port"], data["repl_out_port"]) == (0, 0)
        assert (data["stdin_port"], data["stdout_port"]) == (0, 0)
        assert data["kernel_host"] == "127.0.0.1"
        written = tmp_path / str(ownership_data.kernel_id) / "config" / "intrinsic-ports.json"
        assert json.loads(written.read_text()) == ports
        assert len(pool) == 10 - 4

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
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            launch_plan,
            resource_spec,
            computers,
            empty,
            pool,
        )

        with pytest.raises(ContainerdImageNotFound):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(pool) == 10
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

        with pytest.raises(ContainerdOperationFailed, match="start_task"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert len(pool) == 10
        assert fake.containers == {}
        assert fake.snapshots == {}
