from __future__ import annotations

import asyncio
import stat
from collections.abc import AsyncIterator, Collection, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, override

import aiodocker
import pytest

from ai.backend.accelerator.mock.plugin import MockPlugin
from ai.backend.accelerator.mock.types import MockDevice
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
)
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.dra.bridge import ContainerEdits
from ai.backend.dra.errors import (
    InvalidClaimUIDError,
    IsolationRequiredError,
    IsolationUnavailableError,
    MissingConsumedSharesError,
    UnknownDeviceError,
    UnsupportedContainerArgsError,
)
from ai.backend.dra.host.isolation import BaiHook, HamiCore, SharedAllocation
from ai.backend.dra.host.plugin_host import (
    PluginHost,
    device_name,
    docker_args_to_edits,
    gpu_uuid,
    pcie_root,
    share_capacity,
)

MOCK_CONFIG = """
slot_name = "cuda"
device_plugin_name = "CUDADevice"
devices = [
  { mother_uuid = "aaaaaaaa-0000-0000-0000-000000000001", model_name = "CUDA GPU", numa_node = 0, subproc_count = 108, memory_size = "40G", is_mig_device = false },
  { mother_uuid = "aaaaaaaa-0000-0000-0000-000000000002", model_name = "CUDA GPU", numa_node = 1, subproc_count = 108, memory_size = "40G", is_mig_device = false },
]
[attributes]
nvidia_driver = "450.0.0"
cuda_runtime = "11.0"
[formats.device]
display_unit = "GPU"
display_icon = "gpu1"
human_readable_name = "GPU"
description = "CUDA-capable GPU"
number_format = { binary = false, round_length = 0 }
"""
GIB = 1024**3
CLAIM = "0b5e6a2c-1d1f-4a8e-9a43-3f1d2b8f0c11"
HAMI = HamiCore(Path("/var/lib/bai-dra/hami-core"))


MIG_CONFIG = MOCK_CONFIG.replace(
    "]\n[attributes]",
    """  { mother_uuid = "aaaaaaaa-0000-0000-0000-000000000003", model_name = "CUDA GPU-1g.10gb", numa_node = 1, subproc_count = 14, memory_size = "10G", is_mig_device = true },
  { mother_uuid = "aaaaaaaa-0000-0000-0000-000000000003", model_name = "CUDA GPU", numa_node = 1, subproc_count = 98, memory_size = "80G", is_mig_device = false },
]
[attributes]""",
)
MIG_ID = "MIG-aaaaaaaa-0000-0000-0000-000000000003/2/0"


class FailingHami(HamiCore):
    """A provider that refuses every allocation: a claim that reaches it fails."""

    def __init__(self) -> None:
        super().__init__(Path("/nonexistent"))

    @override
    async def edits(
        self, allocation: SharedAllocation, plugin: AbstractComputePlugin
    ) -> ContainerEdits:
        raise IsolationUnavailableError("the provider is not reachable")


class CDIMockPlugin(MockPlugin):
    """Names one CDI device of another spec per allocated device, as the CUDA plugin does."""

    @override
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        ids = [f"nvidia.com/gpu={d}" for alloc in device_alloc.values() for d in alloc]
        return {"HostConfig": {"DeviceRequests": [{"Driver": "cdi", "DeviceIDs": ids}]}}


class HookMockPlugin(MockPlugin):
    """Provides hook libraries, as the enterprise CUDA plugin does from its hook cache."""

    hook_dir: Path

    @override
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return [self.hook_dir / "libnvmlhook.so", self.hook_dir / "libcudahook.so"]


class SlowListMockPlugin(MockPlugin):
    """While `relisting`, the device list drops a device and create_alloc_map waits."""

    release: asyncio.Event
    entered: asyncio.Event
    relisting: bool

    @override
    async def list_devices(self) -> Collection[MockDevice]:
        devices = await super().list_devices()
        return list(devices)[:1] if self.relisting else devices

    @override
    async def create_alloc_map(self) -> AbstractAllocMap:
        if self.relisting:
            self.entered.set()
            await self.release.wait()
        return await super().create_alloc_map()


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "mock-accelerator.toml").write_text(MOCK_CONFIG)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
async def mock_host(mock_config_dir: Path) -> AsyncIterator[PluginHost]:
    host = await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "discrete"},
        {},
        mount_root=mock_config_dir / "mounts",
    )
    yield host
    await host.close()


@pytest.fixture
async def shared_host(mock_config_dir: Path) -> AsyncIterator[PluginHost]:
    host = await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "discrete"},
        {},
        mount_root=mock_config_dir / "mounts",
        shared=True,
        isolation=HAMI,
    )
    yield host
    await host.close()


@pytest.fixture
async def mig_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[PluginHost]:
    (tmp_path / "mock-accelerator.toml").write_text(MIG_CONFIG)
    monkeypatch.chdir(tmp_path)
    host = await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "fractional"},
        {},
        mount_root=tmp_path / "mounts",
        shared=True,
        isolation=FailingHami(),
    )
    yield host
    await host.close()


class UUIDMockPlugin(MockPlugin):
    """Knows each GPU's bare UUID, as the CUDA plugin does."""

    @override
    async def list_devices(self) -> Collection[MockDevice]:
        devices = await super().list_devices()
        for d in devices:
            setattr(d, "uuid", str(d.mother_uuid))
        return devices


@pytest.fixture
async def dynamic_mig_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[PluginHost]:
    (tmp_path / "mock-accelerator.toml").write_text(MIG_CONFIG)
    monkeypatch.chdir(tmp_path)
    plugin = UUIDMockPlugin({"allocation_mode": "fractional"}, {})
    await plugin.init()
    host = PluginHost(plugin, tmp_path / "mounts", shared=True, isolation=HAMI, dynamic_mig=True)
    yield host
    await host.close()


@pytest.fixture
async def small_unit_host(mock_config_dir: Path) -> AsyncIterator[PluginHost]:
    host = await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "discrete", "unit_mem": "1g", "unit_proc": 4},
        {},
        mount_root=mock_config_dir / "mounts",
        shared=True,
        isolation=HAMI,
    )
    yield host
    await host.close()


@pytest.fixture
async def cdi_host(mock_config_dir: Path) -> AsyncIterator[PluginHost]:
    plugin = CDIMockPlugin({"allocation_mode": "discrete"}, {})
    await plugin.init()
    host = PluginHost(plugin, mock_config_dir / "mounts")
    yield host
    await host.close()


@pytest.fixture
async def hook_host(mock_config_dir: Path) -> AsyncIterator[PluginHost]:
    plugin = HookMockPlugin({"allocation_mode": "fractional"}, {})
    plugin.hook_dir = mock_config_dir / "hook"
    await plugin.init()
    host = PluginHost(plugin, mock_config_dir / "mounts", shared=True, isolation=BaiHook())
    yield host
    await host.close()


@pytest.fixture
def fake_sysfs(tmp_path: Path) -> Path:
    device = tmp_path / "devices/pci0000:98/0000:98:01.0/0000:99:00.0"
    device.mkdir(parents=True)
    links = tmp_path / "bus/pci/devices"
    links.mkdir(parents=True)
    (links / "0000:99:00.0").symlink_to(device)
    return tmp_path


class TestDockerArgsToEdits:
    def test_env_devices_and_mounts(self) -> None:
        edits = docker_args_to_edits({
            "Env": ["A=1"],
            "HostConfig": {
                "Devices": [{"PathOnHost": "/dev/x0", "PathInContainer": "/dev/x0"}],
                "Binds": ["/opt/lib:/usr/lib/x:ro"],
            },
        })
        assert edits.env == ["A=1"]
        assert edits.device_nodes[0].host_path == "/dev/x0"
        assert edits.mounts[0].options == ["bind", "ro"]

    def test_rejects_what_cdi_cannot_express(self) -> None:
        with pytest.raises(UnsupportedContainerArgsError):
            docker_args_to_edits({"HostConfig": {"Runtime": "nvidia"}})

    def test_cdi_requests_pass_through(self) -> None:
        edits = docker_args_to_edits({
            "HostConfig": {
                "DeviceRequests": [{"Driver": "cdi", "DeviceIDs": ["nvidia.com/gpu=GPU-1"]}]
            }
        })
        assert edits.cdi_devices == ["nvidia.com/gpu=GPU-1"]

    def test_other_device_drivers_are_rejected(self) -> None:
        with pytest.raises(UnsupportedContainerArgsError):
            docker_args_to_edits({
                "HostConfig": {"DeviceRequests": [{"Driver": "nvidia", "DeviceIDs": ["0"]}]}
            })


class TestDeviceName:
    def test_is_a_dns_label(self) -> None:
        assert device_name(DeviceId("MIG-ABC/1/0")) == "dev-mig-abc-1-0"


class TestShareCapacity:
    def test_the_smaller_of_memory_and_sms(self) -> None:
        # H100 80GB with the default units: 40 shares by memory, 16.5 by SMs.
        assert share_capacity(80 * GIB, 132, 2 * GIB, 8) == 1650

    def test_rounds_down_to_a_hundredth(self) -> None:
        assert share_capacity(10 * GIB, 1000, 3 * GIB, 8) == 333


class TestPcieRoot:
    def test_reads_the_root_complex_from_sysfs(self, fake_sysfs: Path) -> None:
        assert pcie_root("0000:99:00.0", fake_sysfs) == "pci0000:98"

    def test_unknown_device_has_none(self, fake_sysfs: Path) -> None:
        assert pcie_root("0000:01:00.0", fake_sysfs) is None


class TestPluginHost:
    async def test_lists_mock_devices_with_schema_attributes(self, mock_host: PluginHost) -> None:
        response = await mock_host.list_devices()
        assert response.slot_name == "cuda"
        [first, _] = response.devices
        assert first.attributes["slotName"] == "cuda.device"
        assert first.attributes["numaNode"] == 0
        assert first.capacity["memory"] == str(40 * GIB)

    async def test_publishes_standard_attributes(
        self, mock_config_dir: Path, fake_sysfs: Path
    ) -> None:
        plugin = MockPlugin({"allocation_mode": "discrete"}, {})
        await plugin.init()
        host = PluginHost(plugin, mock_config_dir / "mounts", sysfs_root=fake_sysfs)
        [first, second] = (await host.list_devices()).devices
        await host.close()
        assert first.attributes["resource.kubernetes.io/pciBusID"] == "0000:99:00.0"
        assert first.attributes["resource.kubernetes.io/pcieRoot"] == "pci0000:98"
        assert first.attributes["resource.kubernetes.io/numaNode"] == 0
        assert "resource.kubernetes.io/pcieRoot" not in second.attributes

    async def test_generation_changes_only_with_the_devices(self, mock_host: PluginHost) -> None:
        first = await mock_host.list_devices()
        again = await mock_host.list_devices()
        assert (again.host_id, again.generation) == (first.host_id, first.generation)

    async def test_prepare_returns_the_plugin_injection(self, mock_host: PluginHost) -> None:
        devices = (await mock_host.list_devices()).devices
        edits, _ = await mock_host.prepare(CLAIM, [devices[1].name])
        assert "BACKENDAI_MOCK_CUDA_DEVICE_COUNT=1" in edits.env
        assert "BACKENDAI_MOCK_CUDA_DEVICES=aaaaaaaa-0000-0000-0000-000000000002" in edits.env

    async def test_prepare_rejects_unknown_devices(self, mock_host: PluginHost) -> None:
        with pytest.raises(UnknownDeviceError):
            await mock_host.prepare(CLAIM, ["dev-nope"])

    async def test_prepare_rejects_a_path_as_claim_uid(self, mock_host: PluginHost) -> None:
        with pytest.raises(InvalidClaimUIDError):
            await mock_host.prepare("../../etc", [])

    async def test_unprepare_removes_the_claim_directory(
        self, mock_host: PluginHost, mock_config_dir: Path
    ) -> None:
        devices = (await mock_host.list_devices()).devices
        await mock_host.prepare(CLAIM, [devices[0].name])
        assert (mock_config_dir / "mounts" / CLAIM).is_dir()
        await mock_host.unprepare(CLAIM)
        assert not (mock_config_dir / "mounts" / CLAIM).exists()


class TestCDIDevicesPerDevice:
    async def test_each_device_gets_its_own_cdi_device(self, cdi_host: PluginHost) -> None:
        [first, second] = (await cdi_host.list_devices()).devices
        edits, per_device = await cdi_host.prepare(CLAIM, [first.name, second.name])
        assert per_device == {
            first.name: ["nvidia.com/gpu=aaaaaaaa-0000-0000-0000-000000000001"],
            second.name: ["nvidia.com/gpu=aaaaaaaa-0000-0000-0000-000000000002"],
        }
        assert edits.cdi_devices == []


class TestSharedDevices:
    async def test_shared_without_isolation_is_refused(self, mock_config_dir: Path) -> None:
        with pytest.raises(IsolationRequiredError):
            await PluginHost.start(
                "ai.backend.accelerator.mock.plugin:MockPlugin",
                {"allocation_mode": "discrete"},
                {},
                shared=True,
            )

    async def test_shared_devices_are_allocated_by_the_shares_slot(
        self, shared_host: PluginHost
    ) -> None:
        devices = (await shared_host.list_devices()).devices
        assert {d.attributes["slotName"] for d in devices} == {"cuda.shares"}

    async def test_capacity_is_the_device_share_capacity(self, shared_host: PluginHost) -> None:
        [first, _] = (await shared_host.list_devices()).devices
        # 108 SMs / 8 per share = 13.5 shares (memory allows 20).
        assert first.allow_multiple_allocations
        assert first.capacity == {"shares": "1350"}
        policy = first.request_policies["shares"]
        assert (policy.default, policy.min, policy.max, policy.step) == ("1350", "1", "1350", "1")
        assert first.attributes["memory"] == 40 * GIB

    async def test_capacity_follows_the_plugin_share_units(
        self, small_unit_host: PluginHost
    ) -> None:
        [first, _] = (await small_unit_host.list_devices()).devices
        assert first.capacity == {"shares": "2700"}

    async def test_a_share_is_limited_per_device(self, shared_host: PluginHost) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits, _ = await shared_host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={GIB}" in edits.env
        # 0.5 share → 4 SMs (the minimum) of 108 → 4 %.
        assert "CUDA_DEVICE_SM_LIMIT_0=4" in edits.env
        assert {m.container_path for m in edits.mounts} >= {
            "/usr/local/vgpu/libvgpu.so",
            "/etc/ld.so.preload",
            "/overrideEnv",
        }

    async def test_hami_limits_are_in_a_read_only_override_file(
        self, shared_host: PluginHost, mock_config_dir: Path
    ) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits, _ = await shared_host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        [mount] = [m for m in edits.mounts if m.container_path == "/overrideEnv"]
        override = Path(mount.host_path)
        assert override.parent == mock_config_dir / "mounts" / CLAIM
        assert mount.options == ["bind", "ro"]
        lines = override.read_text().splitlines()
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={GIB}" in lines
        assert "CUDA_DEVICE_SM_LIMIT_0=4" in lines
        assert all("=" in line for line in lines)
        assert not override.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)

    async def test_a_whole_device_runs_without_isolation(
        self, shared_host: PluginHost, mock_config_dir: Path
    ) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits, _ = await shared_host.prepare(CLAIM, [name], {name: {"shares": "1350"}})
        assert not any(e.startswith("CUDA_DEVICE_") for e in edits.env)
        assert not {m.container_path for m in edits.mounts} & {
            "/usr/local/vgpu/libvgpu.so",
            "/etc/ld.so.preload",
            "/overrideEnv",
        }
        assert not (mock_config_dir / "mounts" / CLAIM / "hami-core.env").exists()
        assert "BACKENDAI_MOCK_CUDA_DEVICE_COUNT=1" in edits.env

    async def test_whole_devices_need_no_provider(self, mock_config_dir: Path) -> None:
        plugin = MockPlugin({"allocation_mode": "discrete"}, {})
        await plugin.init()
        host = PluginHost(plugin, mock_config_dir / "mounts", shared=True, isolation=FailingHami())
        [first, second] = (await host.list_devices()).devices
        consumed = {first.name: {"shares": "1350"}, second.name: {"shares": "1350"}}
        edits, _ = await host.prepare(CLAIM, [first.name, second.name], consumed)
        await host.close()
        assert "BACKENDAI_MOCK_CUDA_DEVICE_COUNT=2" in edits.env

    async def test_a_whole_device_beside_a_partial_one_gets_full_limits(
        self, shared_host: PluginHost
    ) -> None:
        [first, second] = (await shared_host.list_devices()).devices
        edits, _ = await shared_host.prepare(
            CLAIM,
            [first.name, second.name],
            {first.name: {"shares": "1350"}, second.name: {"shares": "50"}},
        )
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={40 * GIB}" in edits.env
        assert "CUDA_DEVICE_SM_LIMIT_0=100" in edits.env
        assert f"CUDA_DEVICE_MEMORY_LIMIT_1={GIB}" in edits.env
        assert "CUDA_DEVICE_SM_LIMIT_1=4" in edits.env

    async def test_the_qualified_capacity_name_and_suffixes_are_accepted(
        self, shared_host: PluginHost
    ) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits, _ = await shared_host.prepare(CLAIM, [name], {name: {"dra.backend.ai/shares": "1k"}})
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={20 * GIB}" in edits.env

    async def test_limits_are_indexed_in_device_order(self, shared_host: PluginHost) -> None:
        [first, second] = (await shared_host.list_devices()).devices
        edits, _ = await shared_host.prepare(
            CLAIM,
            [second.name, first.name],
            {first.name: {"shares": "100"}, second.name: {"shares": "200"}},
        )
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={2 * GIB}" in edits.env
        assert f"CUDA_DEVICE_MEMORY_LIMIT_1={4 * GIB}" in edits.env

    async def test_a_shared_device_without_consumed_shares_is_refused(
        self, shared_host: PluginHost
    ) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        with pytest.raises(MissingConsumedSharesError):
            await shared_host.prepare(CLAIM, [name], {})

    async def test_more_than_the_capacity_is_refused(self, shared_host: PluginHost) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        with pytest.raises(MissingConsumedSharesError):
            await shared_host.prepare(CLAIM, [name], {name: {"shares": "1351"}})


class TestStaticMIG:
    async def test_mig_instances_are_exclusive_devices_of_their_slot(
        self, mig_host: PluginHost
    ) -> None:
        devices = {d.attributes["deviceId"]: d for d in (await mig_host.list_devices()).devices}
        mig = devices[MIG_ID]
        assert mig.attributes["slotName"] == "cuda.device:1g.10gb-mig"
        assert not mig.allow_multiple_allocations
        assert mig.request_policies == {}
        assert "shares" not in mig.capacity

    async def test_a_gpu_in_mig_mode_is_not_shared(self, mig_host: PluginHost) -> None:
        devices = (await mig_host.list_devices()).devices
        shared = {d.attributes["deviceId"] for d in devices if d.allow_multiple_allocations}
        assert shared == {
            "aaaaaaaa-0000-0000-0000-000000000001",
            "aaaaaaaa-0000-0000-0000-000000000002",
        }
        assert {d.attributes["slotName"] for d in devices} == {
            "cuda.shares",
            "cuda.device:1g.10gb-mig",
        }

    async def test_a_mig_instance_is_prepared_without_shares_or_isolation(
        self, mig_host: PluginHost
    ) -> None:
        devices = {d.attributes["deviceId"]: d for d in (await mig_host.list_devices()).devices}
        edits, _ = await mig_host.prepare(CLAIM, [devices[MIG_ID].name], {})
        assert f"BACKENDAI_MOCK_CUDA_DEVICES={MIG_ID}" in edits.env


class TestDynamicMIG:
    async def test_whole_gpus_only_and_their_uuids(self, dynamic_mig_host: PluginHost) -> None:
        devices = (await dynamic_mig_host.list_devices()).devices
        assert {d.attributes["slotName"] for d in devices} == {"cuda.shares"}
        # The GPU in MIG mode stays a shared device; the Go driver publishes its MIG devices.
        assert {d.uuid for d in devices} == {
            f"GPU-aaaaaaaa-0000-0000-0000-00000000000{i}" for i in (1, 2, 3)
        }
        assert all(d.allow_multiple_allocations for d in devices)

    async def test_a_device_missing_from_the_last_list_is_listed_again(
        self, dynamic_mig_host: PluginHost
    ) -> None:
        name = (await dynamic_mig_host.list_devices()).devices[0].name
        # As if the GPU was in MIG mode at the last list and has just left it.
        await dynamic_mig_host.list_devices()
        del dynamic_mig_host._devices[name]
        edits, _ = await dynamic_mig_host.prepare(CLAIM, [name], {name: {"shares": "1000"}})
        assert any(e.startswith("BACKENDAI_MOCK_CUDA_DEVICES=") for e in edits.env)

    def test_gpu_uuid_takes_the_nvml_form(self) -> None:
        class Device:
            uuid: str | None

            def __init__(self, uuid: str | None) -> None:
                self.uuid = uuid

        def of(uuid: str | None) -> str | None:
            return gpu_uuid(cast(AbstractComputeDevice, Device(uuid)))

        assert of("1234") == "GPU-1234"
        assert of("GPU-1234") == "GPU-1234"
        assert of("MIG-1234") == "MIG-1234"
        assert of(None) is None


class TestBaiHook:
    async def test_limits_are_hook_env_keyed_by_device(self, hook_host: PluginHost) -> None:
        name = (await hook_host.list_devices()).devices[0].name
        edits, _ = await hook_host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        uuid = "aaaaaaaa-0000-0000-0000-000000000001"
        assert f"BACKEND_CUDA_MEMORY_LIMITS={uuid}:{GIB}" in edits.env
        # 0.5 share → 4 SMs (MIN_SMP_COUNT), an absolute count for the hook.
        assert f"BACKEND_CUDA_PROCESSOR_LIMITS={uuid}:4" in edits.env
        assert "BACKEND_CUDA_RESOURCE_VIRTUALIZED=1" in edits.env
        assert f"BACKEND_CUDA.SHARES_SHARES={uuid}:0.5" in edits.env
        assert f"BACKEND_CUDA_RESERVED_MEMORY={64 * 1024**2}" in edits.env

    async def test_the_plugin_hooks_are_preloaded_read_only(
        self, hook_host: PluginHost, mock_config_dir: Path
    ) -> None:
        name = (await hook_host.list_devices()).devices[0].name
        edits, _ = await hook_host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        mounts = {m.container_path: m for m in edits.mounts}
        hook = mounts["/usr/local/bai-hook/libnvmlhook.so"]
        assert hook.host_path == str(mock_config_dir / "hook" / "libnvmlhook.so")
        preload = mounts["/etc/ld.so.preload"]
        assert all(m.options == ["bind", "ro"] for m in mounts.values())
        # NVML first, as the plugin orders them.
        assert Path(preload.host_path).read_text().splitlines() == [
            "/usr/local/bai-hook/libnvmlhook.so",
            "/usr/local/bai-hook/libcudahook.so",
        ]
        assert not any(e.startswith("LD_PRELOAD=") for e in edits.env)

    async def test_a_plugin_without_limits_is_refused(self, mock_config_dir: Path) -> None:
        # The discrete mode gives no CUDA_*_LIMITS: the device would be unlimited.
        plugin = HookMockPlugin({"allocation_mode": "discrete"}, {})
        plugin.hook_dir = mock_config_dir / "hook"
        await plugin.init()
        host = PluginHost(plugin, mock_config_dir / "mounts", shared=True, isolation=BaiHook())
        name = (await host.list_devices()).devices[0].name
        with pytest.raises(IsolationUnavailableError):
            await host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        await host.close()

    async def test_a_plugin_without_hooks_is_refused(self, mock_config_dir: Path) -> None:
        plugin = MockPlugin({"allocation_mode": "fractional"}, {})
        await plugin.init()
        host = PluginHost(plugin, mock_config_dir / "mounts", shared=True, isolation=BaiHook())
        name = (await host.list_devices()).devices[0].name
        with pytest.raises(IsolationUnavailableError):
            await host.prepare(CLAIM, [name], {name: {"shares": "50"}})
        await host.close()


class TestDeviceListRace:
    async def test_a_prepare_during_a_relist_sees_one_generation(
        self, mock_config_dir: Path
    ) -> None:
        plugin = SlowListMockPlugin({"allocation_mode": "discrete"}, {})
        plugin.release, plugin.entered, plugin.relisting = asyncio.Event(), asyncio.Event(), False
        await plugin.init()
        host = PluginHost(plugin, mock_config_dir / "mounts")
        [_, second] = (await host.list_devices()).devices
        plugin.relisting = True
        relist = asyncio.create_task(host.list_devices())
        await plugin.entered.wait()
        # The relist has the new device list but not its slots yet: the old maps still serve.
        edits, _ = await host.prepare(CLAIM, [second.name])
        assert "BACKENDAI_MOCK_CUDA_DEVICE_COUNT=1" in edits.env
        plugin.release.set()
        assert len((await relist).devices) == 1
        with pytest.raises(UnknownDeviceError):
            await host.prepare(CLAIM, [second.name])
        await host.close()
