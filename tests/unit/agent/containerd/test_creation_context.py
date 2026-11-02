from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.client import MountSpec
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    KernelNetworkSetupFailed,
    KernelVerbNotSupported,
)
from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData, MountInfo
from ai.backend.common.types import (
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    MountTypes,
    ResourceSlot,
    ServicePort,
    ServicePortProtocols,
    SlotName,
)

from .fakes import FakeCommandRunner, FakeContainerd


def _local_config(scratch_root: Path) -> MagicMock:
    config = MagicMock()
    config.container.scratch_root = scratch_root
    config.container.kernel_uid = 1000
    config.container.kernel_gid = 1000
    config.container.sandbox_type = "docker"
    config.debug.coredump.enabled = False
    return config


def _make_context(
    ownership_data: KernelOwnershipData,
    kernel_config: KernelCreationConfig,
    *,
    scratch_root: Path,
    client: FakeContainerd | None = None,
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
        client=client or FakeContainerd(),
        network=network or KernelNetwork(run=runner or FakeCommandRunner()),
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
    async def test_base_spec_carries_the_kernel_resources(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            scratch_root=tmp_path,
            computers=computers,
        )
        await ctx.prepare_scratch()

        kernel = await ctx.prepare_container(resource_spec, {"A": "1"}, [], MagicMock())

        assert isinstance(kernel, ContainerdKernel)
        base_spec = ctx._base_spec
        assert base_spec["linux"]["resources"]["cpu"]["cpus"] == "1,3"
        assert base_spec["linux"]["resources"]["memory"]["limit"] == 1073741824
        assert base_spec["hostname"] == "main1"
        assert base_spec["linux"]["namespaces"][4] == {
            "type": "network",
            "path": f"/run/netns/bai-{ownership_data.kernel_id}",
        }

    async def test_config_files_are_written_for_the_kernel_runner(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            scratch_root=tmp_path,
            computers=computers,
        )
        await ctx.prepare_scratch()

        await ctx.prepare_container(resource_spec, {"A": "1", "B": "2"}, [], MagicMock())

        config_dir = tmp_path / str(ownership_data.kernel_id) / "config"
        assert (config_dir / "environ.txt").read_text() == "A=1\nB=2\n"
        assert "CPU_SHARES=1:1,3:1" in (config_dir / "resource.txt").read_text()

    async def test_setup_failing_part_way_removes_the_netns(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        runner = FakeCommandRunner()
        ns = f"bai-{ownership_data.kernel_id}"
        runner.script(["ip", "netns", "list"], f"{ns}\n")
        runner.failing.add(("ip", "-n"))
        ctx = _make_context(
            ownership_data,
            launch_kernel_config,
            scratch_root=tmp_path,
            computers=computers,
            runner=runner,
        )
        await ctx.prepare_scratch()

        with pytest.raises(KernelNetworkSetupFailed):
            await ctx.prepare_container(resource_spec, {}, [], MagicMock())

        assert ("ip", "netns", "del", ns) in runner.calls


class TestCreationContextMembers:
    def test_repl_ports_and_protected_services_stay_unsupported(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(ownership_data, kernel_config, scratch_root=tmp_path)

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
        ctx = _make_context(ownership_data, kernel_config, scratch_root=tmp_path)

        assert await ctx.get_extra_envs() == {}

    async def test_resource_spec_requires_cpu(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        config = cast(KernelCreationConfig, {**kernel_config, "resource_slots": {"mem": "1"}})
        ctx = _make_context(ownership_data, config, scratch_root=tmp_path)

        with pytest.raises(UnsupportedResource):
            await ctx.prepare_resource_spec()

    async def test_apply_network_is_a_noop(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(ownership_data, kernel_config, scratch_root=tmp_path)

        await ctx.apply_network(MagicMock())


class TestIntrinsicMounts:
    async def test_config_is_read_only_and_work_is_writable(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        ctx = _make_context(ownership_data, kernel_config, scratch_root=tmp_path)

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
    def ctx(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> ContainerdKernelCreationContext:
        return _make_context(
            ownership_data,
            launch_kernel_config,
            scratch_root=tmp_path,
            client=fake,
            computers=computers,
        )

    @pytest.mark.parametrize("slot", ["cpu", "mem"])
    async def test_intrinsic_slots_are_accepted(
        self,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
        resource_spec: KernelResourceSpec,
        slot: str,
    ) -> None:
        alloc = {SlotName(slot): {DeviceId("root"): Decimal(1)}}
        await ctx.prepare_scratch()

        await ctx.apply_accelerator_allocation(_accelerator_plugin(slot, {}), alloc)
        await ctx.prepare_container(resource_spec, {}, [], MagicMock())

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

    async def test_plugin_with_container_arguments_is_refused_and_removes_the_scratch(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        ctx: ContainerdKernelCreationContext,
        fake: FakeContainerd,
    ) -> None:
        await ctx.prepare_scratch()
        fragment = {"HostConfig": {"Devices": [{"PathOnHost": "/dev/nvidia0"}]}}
        plugin = _accelerator_plugin("cuda", fragment)
        alloc = {SlotName("cuda.shares"): {DeviceId("0"): Decimal(1)}}

        with pytest.raises(KernelVerbNotSupported, match="cuda"):
            await ctx.apply_accelerator_allocation(plugin, alloc)

        assert not (tmp_path / str(ownership_data.kernel_id)).exists()
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
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        client: FakeContainerd,
        runner: FakeCommandRunner | None = None,
        service_ports: list[ServicePort] | None = None,
    ) -> tuple[ContainerdKernelCreationContext, ContainerdKernel]:
        ctx = _make_context(
            ownership_data,
            kernel_config,
            scratch_root=tmp_path,
            client=client,
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
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
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
            f"/run/netns/bai-{ownership_data.kernel_id}"
        )

    async def test_the_container_runs_on_runc(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert fake.runtimes[data["container_id"]] == "io.containerd.runc.v2"

    async def test_labels_identify_the_kernel_and_its_owner(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        labels = fake.containers[data["container_id"]].labels
        assert labels["ai.backend.kernel-id"] == str(ownership_data.kernel_id)
        assert labels["ai.backend.session-id"] == str(ownership_data.session_id)
        assert labels["ai.backend.owner"] == str(ownership_data.agent_id)
        assert labels[CONFIG_DIR_LABEL] == str(
            (tmp_path / str(ownership_data.kernel_id)).resolve() / "config"
        )

    async def test_cgroup_path_is_namespaced_by_container_id(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
        )

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        spec = fake.specs[data["container_id"]]
        assert spec["linux"]["cgroupsPath"] == f"/{fake.namespace}/{data['container_id']}"

    async def test_no_port_is_published(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
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
            resource_spec,
            computers,
            fake,
            runner,
            sports,
        )

        runner.calls.clear()

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert data == {"container_id": data["container_id"]}
        assert [sport["host_ports"] for sport in sports] == [(None,), (None, None)]
        assert runner.calls == []

    async def test_network_is_set_up_before_the_task_is_created(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        runner = FakeCommandRunner(fake.calls)
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
            runner,
        )

        await ctx.start_container(kernel, [], None, [], MagicMock())

        ops = [op for op, _ in fake.calls]
        assert ops.index("cmd") < ops.index("create_task")
        assert "ip -n bai-" in " ".join(key for op, key in fake.calls if op == "cmd")

    async def test_task_stdio_goes_to_the_scratch_log_file(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        fake = StdioRecordingContainerd()
        fake.add_image(self.image_ref, diff_ids=["sha256:aa"])
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
        )

        await ctx.start_container(kernel, [], None, [], MagicMock())

        expected = f"file://{(tmp_path / str(ownership_data.kernel_id)).resolve()}/task.log"
        assert fake.stdio == [expected, expected]

    async def test_each_launch_attempt_gets_a_fresh_container_id(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
        )

        first = await ctx.start_container(kernel, [], None, [], MagicMock())
        second = await ctx.start_container(kernel, [], None, [], MagicMock())

        assert first["container_id"] != second["container_id"]

    async def test_missing_image_removes_the_netns_and_frees_allocations(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
    ) -> None:
        empty = FakeContainerd()
        runner = FakeCommandRunner()
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            empty,
            runner,
        )

        with pytest.raises(ContainerdImageNotFound):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert runner.matching("ip", "netns", "list")  # the netns teardown ran
        assert empty.containers == {}
        cast(MagicMock, computers[DeviceName("cpu")].alloc_map).free.assert_called_once()
        cast(MagicMock, computers[DeviceName("mem")].alloc_map).free.assert_called_once()

    async def test_launch_failure_leaves_no_container_and_no_netns(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
    ) -> None:
        fake.failing.add("start_task")
        runner = FakeCommandRunner()
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
            runner,
        )

        with pytest.raises(ContainerdOperationFailed, match="start_task"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert fake.containers == {}
        assert fake.snapshots == {}
        assert runner.matching("ip", "netns", "list")  # the netns teardown ran

    async def test_cancellation_leaves_no_container_and_no_netns(
        self,
        tmp_path: Path,
        ownership_data: KernelOwnershipData,
        launch_kernel_config: KernelCreationConfig,
        resource_spec: KernelResourceSpec,
        computers: dict[DeviceName, ComputerContext],
        fake: FakeContainerd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A cancel of the launch after the task was created rolls back like a failure."""
        runner = FakeCommandRunner()
        ctx, kernel = await self._prepared(
            tmp_path,
            ownership_data,
            launch_kernel_config,
            resource_spec,
            computers,
            fake,
            runner,
        )
        create_task = fake.create_task

        async def create_task_then_cancelled(*args: Any, **kwargs: Any) -> Any:
            await create_task(*args, **kwargs)
            raise asyncio.CancelledError

        monkeypatch.setattr(fake, "create_task", create_task_then_cancelled)

        with pytest.raises(asyncio.CancelledError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        assert fake.containers == {}
        assert fake.tasks == {}
        assert fake.snapshots == {}
        assert runner.matching("ip", "netns", "list")  # the netns teardown ran
        cast(MagicMock, computers[DeviceName("cpu")].alloc_map).free.assert_called_once()
