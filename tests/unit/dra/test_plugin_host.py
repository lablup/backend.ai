from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, override

import aiodocker
import pytest

from ai.backend.accelerator.mock.plugin import MockPlugin
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.dra.errors import (
    InvalidClaimUIDError,
    IsolationRequiredError,
    MissingConsumedSharesError,
    UnknownDeviceError,
    UnsupportedContainerArgsError,
)
from ai.backend.dra.host.isolation import HamiCore
from ai.backend.dra.host.plugin_host import (
    PluginHost,
    device_name,
    docker_args_to_edits,
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
        }

    async def test_the_whole_capacity_is_still_isolated(self, shared_host: PluginHost) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits, _ = await shared_host.prepare(CLAIM, [name], {name: {"shares": "1350"}})
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={27 * GIB}" in edits.env
        assert "CUDA_DEVICE_SM_LIMIT_0=100" in edits.env

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
