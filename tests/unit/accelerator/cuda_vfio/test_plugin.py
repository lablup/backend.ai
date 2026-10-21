from __future__ import annotations

import logging
from collections.abc import Iterator
from decimal import Decimal
from importlib.metadata import EntryPoint
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.containers import DockerContainer
from pytest_mock import MockerFixture

from ai.backend.accelerator.cuda_vfio.plugin import CUDAVFIOPlugin
from ai.backend.accelerator.cuda_vfio.sysfs import VFIODeviceUnavailable
from ai.backend.agent.affinity_map import AffinityHint, AffinityMap, AffinityPolicy
from ai.backend.agent.errors import InsufficientResource
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.agent.resources import DiscretePropertyAllocMap, KernelResourceSpec
from ai.backend.agent.types import Container
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import (
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.plugin.entrypoint import scan_entrypoints

NVIDIA = "0x10de"
CLASS_3D = "0x030200"
CLASS_VGA = "0x030000"
CLASS_3D_PROG_IF = "0x030201"
CLASS_BRIDGE = "0x060400"
CLASS_AUDIO = "0x040300"
GPU_BDF = "0001:0b:00.0"
GPU_ID = "0001-0b-00.0"
GPU2_ID = "0001-0c-00.0"


class FakeSysfs:
    """A fake sysfs/dev tree that mirrors the layout the plugin reads."""

    def __init__(self, root: Path) -> None:
        self.sysfs = root / "sys"
        self.dev = root / "dev"
        (self.sysfs / "bus" / "pci" / "devices").mkdir(parents=True)
        (self.sysfs / "kernel" / "iommu_groups").mkdir(parents=True)
        (self.dev / "vfio" / "devices").mkdir(parents=True)

    def add_pci(
        self,
        bdf: str,
        *,
        vendor: str = NVIDIA,
        pci_class: str = CLASS_3D,
        device: str = "0x2bb5",
        driver: str | None = "vfio-pci",
        group: int,
        vfio_node: str | None = None,
        numa_node: int = 1,
    ) -> None:
        pci_dir = self.sysfs / "bus" / "pci" / "devices" / bdf
        pci_dir.mkdir()
        (pci_dir / "vendor").write_text(f"{vendor}\n")
        (pci_dir / "class").write_text(f"{pci_class}\n")
        (pci_dir / "device").write_text(f"{device}\n")
        (pci_dir / "numa_node").write_text(f"{numa_node}\n")
        if driver is not None:
            (pci_dir / "driver").symlink_to(self.sysfs / "bus" / "pci" / "drivers" / driver)
        group_dir = self.sysfs / "kernel" / "iommu_groups" / str(group)
        (group_dir / "devices").mkdir(parents=True, exist_ok=True)
        (pci_dir / "iommu_group").symlink_to(group_dir)
        (group_dir / "devices" / bdf).symlink_to(pci_dir)
        if vfio_node is not None:
            (pci_dir / "vfio-dev" / vfio_node).mkdir(parents=True)
            (self.dev / "vfio" / "devices" / vfio_node).touch()


@pytest.fixture
def fake_sysfs(tmp_path: Path) -> FakeSysfs:
    return FakeSysfs(tmp_path)


def _make_plugin(fake: FakeSysfs, plugin_config: dict[str, Any] | None = None) -> CUDAVFIOPlugin:
    plugin = CUDAVFIOPlugin.__new__(CUDAVFIOPlugin)
    plugin.plugin_config = plugin_config or {}
    plugin.local_config = {}
    plugin.enabled = True
    plugin.memory_overrides = {}
    plugin.sysfs_root = fake.sysfs
    plugin.dev_root = fake.dev
    return plugin


class TestListDevices:
    """Tests for CUDAVFIOPlugin.list_devices against a fake sysfs tree."""

    async def test_offers_a_gpu_alone_in_its_group(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs)

        devices = list(await plugin.list_devices())

        assert len(devices) == 1
        dev = devices[0]
        assert dev.device_id == DeviceId(GPU_ID)
        assert dev.hw_location == GPU_BDF
        assert dev.iommu_group == 84
        assert dev.vfio_node == "/dev/vfio/devices/vfio0"
        assert dev.numa_node == 1
        assert dev.processing_units == 0
        assert dev.memory_size == 96 * 1024**3

    async def test_refuses_a_gpu_whose_group_has_a_non_vfio_member(
        self, fake_sysfs: FakeSysfs, caplog: pytest.LogCaptureFixture
    ) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        fake_sysfs.add_pci(
            "0001:0b:00.1", vendor=NVIDIA, pci_class=CLASS_AUDIO, driver="snd_hda_intel", group=84
        )
        plugin = _make_plugin(fake_sysfs)

        with caplog.at_level(logging.WARNING):
            devices = await plugin.list_devices()

        assert devices == []
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert [getattr(r, "log_tag_member", None) for r in warnings] == ["0001:0b:00.1"]

    async def test_refuses_a_gpu_whose_group_directory_is_unreadable(
        self, fake_sysfs: FakeSysfs, caplog: pytest.LogCaptureFixture
    ) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        group_devices = fake_sysfs.sysfs / "kernel" / "iommu_groups" / "84" / "devices"
        (group_devices / GPU_BDF).unlink()
        group_devices.rmdir()
        plugin = _make_plugin(fake_sysfs)

        with caplog.at_level(logging.WARNING):
            devices = await plugin.list_devices()

        assert devices == []
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert [r.getMessage() for r in warnings] == ["GPU skipped, IOMMU group members unreadable"]
        assert getattr(warnings[0], "log_tag_member", None) is None

    @pytest.mark.parametrize("pci_class", [CLASS_3D, CLASS_VGA, CLASS_3D_PROG_IF])
    async def test_offers_gpus_regardless_of_prog_if(
        self, fake_sysfs: FakeSysfs, pci_class: str
    ) -> None:
        fake_sysfs.add_pci(GPU_BDF, pci_class=pci_class, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs)

        assert [d.device_id for d in await plugin.list_devices()] == [DeviceId(GPU_ID)]

    async def test_ignores_nvidia_device_of_another_class(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, pci_class=CLASS_AUDIO, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.list_devices() == []

    async def test_negative_numa_node_is_none(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0", numa_node=-1)
        plugin = _make_plugin(fake_sysfs)

        devices = list(await plugin.list_devices())

        assert devices[0].numa_node is None

    async def test_offers_a_gpu_sharing_its_group_with_a_bridge(
        self, fake_sysfs: FakeSysfs
    ) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        fake_sysfs.add_pci(
            "0001:0a:00.0", vendor="0x1000", pci_class=CLASS_BRIDGE, driver="pcieport", group=84
        )
        plugin = _make_plugin(fake_sysfs)

        devices = await plugin.list_devices()

        assert [d.device_id for d in devices] == [DeviceId(GPU_ID)]

    async def test_ignores_non_nvidia_device_bound_to_vfio(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci("0000:0b:00.0", vendor="0x20a6", group=3, vfio_node="vfio1")
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.list_devices() == []

    async def test_ignores_nvidia_device_with_another_driver(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, driver="nvidia", group=84)
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.list_devices() == []

    async def test_ignores_nvidia_device_without_driver(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, driver=None, group=84)
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.list_devices() == []

    async def test_skips_gpu_without_iommufd_node(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84)
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.list_devices() == []

    @pytest.mark.parametrize("key", [GPU_BDF, GPU_ID])
    async def test_memory_override_by_bdf(self, fake_sysfs: FakeSysfs, key: str) -> None:
        fake_sysfs.add_pci(GPU_BDF, device="0xffff", group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs, {"memory_overrides": {key: 1024}})
        await plugin.init()

        devices = list(await plugin.list_devices())

        assert devices[0].memory_size == 1024

    @pytest.mark.parametrize("key", ["2bb5", "0x2bb5", "0X2BB5"])
    async def test_memory_override_by_device_id(self, fake_sysfs: FakeSysfs, key: str) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs, {"memory_overrides": {key: "48g"}})
        await plugin.init()

        devices = list(await plugin.list_devices())

        assert devices[0].memory_size == 48 * 1024**3

    async def test_bdf_override_wins_over_device_id_override(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs, {"memory_overrides": {"0x2bb5": "48g", GPU_BDF: "24g"}})
        await plugin.init()

        devices = list(await plugin.list_devices())

        assert devices[0].memory_size == 24 * 1024**3

    async def test_bad_memory_override_disables_the_plugin(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs, {"memory_overrides": {"2bb5": "lots"}})

        await plugin.init()

        assert plugin.enabled is False
        assert await plugin.list_devices() == []

    async def test_returns_nothing_when_disabled(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs)
        plugin.enabled = False

        assert await plugin.list_devices() == []
        assert await plugin.generate_docker_args(AsyncMock(), {}) == {}

    async def test_init_keeps_plugin_enabled_with_a_usable_device(
        self, fake_sysfs: FakeSysfs
    ) -> None:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        plugin = _make_plugin(fake_sysfs)

        await plugin.init()

        assert plugin.enabled is True

    async def test_init_disables_plugin_without_usable_device(self, fake_sysfs: FakeSysfs) -> None:
        plugin = _make_plugin(fake_sysfs)

        await plugin.init()

        assert plugin.enabled is False


class TestAllocation:
    """Tests for slot accounting and the container hand-off."""

    @pytest.fixture
    def plugin(self, fake_sysfs: FakeSysfs) -> CUDAVFIOPlugin:
        fake_sysfs.add_pci(GPU_BDF, group=84, vfio_node="vfio0")
        fake_sysfs.add_pci("0001:0c:00.0", group=85, vfio_node="vfio1")
        return _make_plugin(fake_sysfs)

    async def test_available_slots_counts_whole_devices(self, plugin: CUDAVFIOPlugin) -> None:
        assert await plugin.available_slots() == {SlotName("cuda.device"): Decimal(2)}

    async def test_alloc_map_allocates_and_frees_devices(self, plugin: CUDAVFIOPlugin) -> None:
        alloc_map = await plugin.create_alloc_map()
        slot = SlotName("cuda.device")

        assert alloc_map.device_slots[DeviceId(GPU_ID)].slot_type == SlotTypes.COUNT
        alloc = alloc_map.allocate({slot: Decimal(1)})
        assert sum(alloc[slot].values()) == Decimal(1)
        assert len(alloc[slot]) == 1

        alloc_map.free(alloc)

        assert all(v == 0 for v in alloc_map.allocations[slot].values())

    async def test_devices_are_named_after_the_slot_prefix(self, plugin: CUDAVFIOPlugin) -> None:
        devices = await plugin.list_devices()

        assert {dev.device_name for dev in devices} == {DeviceName("cuda")}

    async def test_alloc_map_allocates_with_an_affinity_hint(self, plugin: CUDAVFIOPlugin) -> None:
        devices = await plugin.list_devices()
        affinity_map = AffinityMap.build(list(devices))
        alloc_map = await plugin.create_alloc_map()
        slot = SlotName("cuda.device")

        alloc = alloc_map.allocate(
            {slot: Decimal(1)},
            affinity_hint=AffinityHint(None, affinity_map, AffinityPolicy.PREFER_SINGLE_NODE),
        )

        assert set(alloc) == {slot}
        assert len(alloc[slot]) == 1
        assert sum(alloc[slot].values()) == Decimal(1)

    async def test_alloc_map_rejects_more_devices_than_available(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        alloc_map = await plugin.create_alloc_map()

        with pytest.raises(InsufficientResource):
            alloc_map.allocate({SlotName("cuda.device"): Decimal(3)})

    async def test_generate_docker_args_emits_only_host_config_devices(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        device_alloc = {SlotName("cuda.device"): {DeviceId(GPU_ID): Decimal(1)}}

        args = await plugin.generate_docker_args(AsyncMock(), device_alloc)

        assert args == {
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

    async def test_generate_docker_args_resolves_vfio_node_through_device_id(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        device_alloc = {SlotName("cuda.device"): {DeviceId(GPU2_ID): Decimal(1)}}

        args = await plugin.generate_docker_args(AsyncMock(), device_alloc)

        assert [d["PathOnHost"] for d in args["HostConfig"]["Devices"]] == [
            "/dev/vfio/devices/vfio1"
        ]

    async def test_generate_docker_args_rejects_bdf_as_device_id(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        device_alloc = {SlotName("cuda.device"): {DeviceId(GPU_BDF): Decimal(1)}}

        with pytest.raises(InvalidResourceArgument):
            await plugin.generate_docker_args(AsyncMock(), device_alloc)

    async def test_resource_txt_round_trip_restores_the_allocation(
        self, plugin: CUDAVFIOPlugin, mocker: MockerFixture
    ) -> None:
        device_id = min(d.device_id for d in await plugin.list_devices())
        spec = KernelResourceSpec(
            ResourceSlot.from_json({"cuda.device": "1"}),
            allocations={
                DeviceName("cuda"): {SlotName("cuda.device"): {device_id: Decimal(1)}},
            },
            scratch_disk_size=0,
            mounts=[],
        )

        restored = KernelResourceSpec.read_from_string(spec.write_to_string())

        assert restored.allocations == spec.allocations
        mocker.patch(
            "ai.backend.accelerator.cuda_vfio.plugin.get_resource_spec_from_container",
            AsyncMock(return_value=restored),
        )
        alloc_map = await plugin.create_alloc_map()
        assert isinstance(alloc_map, DiscretePropertyAllocMap)
        await plugin.restore_from_container(self._container({}), alloc_map)
        allocations = alloc_map.allocations[SlotName("cuda.device")]
        assert allocations[DeviceId(GPU_ID)] == Decimal(1)
        assert allocations[DeviceId(GPU2_ID)] == Decimal(0)

    @staticmethod
    def _container(backend_obj: object) -> Container:
        return Container(
            id=ContainerId("c1"),
            status=ContainerStatus.RUNNING,
            image="img",
            labels={},
            ports=[],
            backend_obj=backend_obj,
        )

    @staticmethod
    def _write_resource_txt(config_dir: Path, device_id: DeviceId) -> None:
        config_dir.mkdir()
        spec = KernelResourceSpec(
            ResourceSlot.from_json({"cuda.device": "1"}),
            allocations={
                DeviceName("cuda"): {SlotName("cuda.device"): {device_id: Decimal(1)}},
            },
            scratch_disk_size=0,
            mounts=[],
        )
        (config_dir / "resource.txt").write_text(spec.write_to_string())

    async def test_restore_reads_resource_txt_of_a_docker_container(
        self, plugin: CUDAVFIOPlugin, tmp_path: Path
    ) -> None:
        """The docker agent passes an aiodocker DockerContainer, which is not a Mapping."""
        config_dir = tmp_path / "config"
        self._write_resource_txt(config_dir, DeviceId(GPU2_ID))
        backend_obj = DockerContainer(
            MagicMock(),
            Id="c1",
            Mounts=[{"Target": "/home/config", "Source": str(config_dir)}],
        )
        alloc_map = await plugin.create_alloc_map()

        await plugin.restore_from_container(self._container(backend_obj), alloc_map)

        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId(GPU2_ID)] == Decimal(1)

    async def test_restore_reads_resource_txt_of_an_inspect_mapping(
        self, plugin: CUDAVFIOPlugin, tmp_path: Path
    ) -> None:
        config_dir = tmp_path / "config"
        self._write_resource_txt(config_dir, DeviceId(GPU2_ID))
        backend_obj = {"Mounts": [{"Target": "/home/config", "Source": str(config_dir)}]}
        alloc_map = await plugin.create_alloc_map()

        await plugin.restore_from_container(self._container(backend_obj), alloc_map)

        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId(GPU2_ID)] == Decimal(1)

    async def test_restore_of_a_non_docker_container_leaves_the_map_untouched(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        """A containerd record is neither a DockerContainer nor a Mapping; restore must not raise."""
        alloc_map = await plugin.create_alloc_map()
        slot = SlotName("cuda.device")
        picked = alloc_map.allocate({slot: Decimal(1)})
        containerd_record = object()

        await plugin.restore_from_container(self._container(containerd_record), alloc_map)

        (device_id,) = picked[slot]
        assert alloc_map.allocations[slot][device_id] == Decimal(1)
        assert sum(alloc_map.allocations[slot].values()) == Decimal(1)

    async def test_generate_docker_args_skips_unallocated_devices(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        device_alloc = {
            SlotName("cuda.device"): {
                DeviceId(GPU_ID): Decimal(0),
                DeviceId(GPU2_ID): Decimal(1),
            }
        }

        args = await plugin.generate_docker_args(AsyncMock(), device_alloc)

        assert [d["PathOnHost"] for d in args["HostConfig"]["Devices"]] == [
            "/dev/vfio/devices/vfio1"
        ]

    async def test_generate_docker_args_fails_when_cdev_vanished(
        self, plugin: CUDAVFIOPlugin, fake_sysfs: FakeSysfs
    ) -> None:
        (fake_sysfs.dev / "vfio" / "devices" / "vfio0").unlink()
        device_alloc = {SlotName("cuda.device"): {DeviceId(GPU_ID): Decimal(1)}}

        with pytest.raises(VFIODeviceUnavailable):
            await plugin.generate_docker_args(AsyncMock(), device_alloc)

    async def test_generate_docker_args_rejects_unknown_device(
        self, plugin: CUDAVFIOPlugin
    ) -> None:
        device_alloc = {SlotName("cuda.device"): {DeviceId("0001-ff-00.0"): Decimal(1)}}

        with pytest.raises(InvalidResourceArgument):
            await plugin.generate_docker_args(AsyncMock(), device_alloc)

    async def test_get_attached_devices(self, plugin: CUDAVFIOPlugin) -> None:
        device_alloc = {SlotName("cuda.device"): {DeviceId(GPU_ID): Decimal(1)}}

        attached = await plugin.get_attached_devices(device_alloc)

        assert [d["device_id"] for d in attached] == [DeviceId(GPU_ID)]
        assert attached[0]["data"]["mem"] == 96 * 1024**3


class TestPluginSurface:
    """Tests for the static plugin contract."""

    async def test_extra_info_reports_iommufd(self, fake_sysfs: FakeSysfs) -> None:
        plugin = _make_plugin(fake_sysfs)

        assert await plugin.extra_info() == {"driver": "vfio-pci", "iommufd": "yes"}

    def test_metadata_and_key(self, fake_sysfs: FakeSysfs) -> None:
        plugin = _make_plugin(fake_sysfs)

        assert plugin.key == "cuda"
        assert plugin.get_metadata()["slot_name"] == "cuda.device"

    def test_loaded_only_with_explicit_allow(self, mocker: MockerFixture) -> None:
        entrypoint = EntryPoint(
            name="cuda_vfio",
            value="ai.backend.accelerator.cuda_vfio.plugin:CUDAVFIOPlugin",
            group="backendai_accelerator_v21",
        )

        def _scan(group: str) -> Iterator[EntryPoint]:
            yield entrypoint

        mocker.patch("ai.backend.plugin.entrypoint.prepare_wheelhouse")
        mocker.patch("ai.backend.plugin.entrypoint.scan_entrypoint_from_buildscript", _scan)
        mocker.patch(
            "ai.backend.plugin.entrypoint.scan_entrypoint_from_package_metadata",
            lambda group: iter(()),
        )
        mocker.patch("ai.backend.common.plugin.scan_entrypoints", scan_entrypoints)

        not_allowed: list[tuple[str, type[AbstractPlugin]]] = list(
            BasePluginContext.discover_plugins("backendai_accelerator_v21", allowlist=None)
        )
        other_prefix: list[tuple[str, type[AbstractPlugin]]] = list(
            BasePluginContext.discover_plugins(
                "backendai_accelerator_v21", allowlist={"ai.backend.accelerator.cuda_open"}
            )
        )
        allowed: list[tuple[str, type[AbstractPlugin]]] = list(
            BasePluginContext.discover_plugins(
                "backendai_accelerator_v21", allowlist={"ai.backend.accelerator.cuda_vfio"}
            )
        )

        assert not_allowed == []
        assert other_prefix == []
        assert [name for name, _ in allowed] == ["cuda_vfio"]
