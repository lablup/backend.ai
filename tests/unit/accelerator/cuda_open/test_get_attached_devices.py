from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from ai.backend.accelerator.cuda_open.plugin import CUDADevice, CUDAPlugin
from ai.backend.common.types import DeviceId, DeviceName, SlotName


def _make_device(device_id: str, model_name: str) -> CUDADevice:
    return CUDADevice(
        device_id=DeviceId(device_id),
        device_name=DeviceName("cuda"),
        model_name=model_name,
        uuid=device_id,
        hw_location="0000:00:1e.0",
        numa_node=0,
        memory_size=1024 * 1024 * 1024 * 8,
        processing_units=64,
    )


class TestGetAttachedDevices:
    """Tests for CUDAPlugin.get_attached_devices."""

    @pytest.fixture
    def devices(self) -> list[CUDADevice]:
        return [
            _make_device("GPU-0", "NVIDIA A100"),
            _make_device("GPU-1", "NVIDIA A100"),
        ]

    @pytest.fixture
    def cuda_plugin(self, devices: list[CUDADevice]) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.plugin_config = {}
        plugin.local_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        plugin.list_devices = AsyncMock(return_value=devices)  # type: ignore[method-assign]
        return plugin

    async def test_returns_devices_allocated_under_the_cuda_device_slot(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """An allocation keyed by the plugin's own slot name must be resolved.

        The slot name here is the singular "cuda.device" that the plugin
        registers in `slot_types` and allocates in `create_alloc_map`; looking
        up any other name silently yields no attached devices.
        """
        device_alloc = {
            SlotName("cuda.device"): {DeviceId("GPU-0"): Decimal(1)},
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert [dev["device_id"] for dev in attached] == [DeviceId("GPU-0")]
        assert attached[0]["model_name"] == "NVIDIA A100"
        assert attached[0]["data"] == {"smp": 64, "mem": 1024 * 1024 * 1024 * 8}

    async def test_slot_name_matches_the_allocated_slot(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """The looked-up slot name must be the one the plugin actually allocates.

        `create_alloc_map()` builds its `DeviceSlotInfo` entries from
        `slot_types[0][0]`, so feeding that exact name in must resolve the
        device. This pins the two sides together regardless of the literal.
        """
        allocated_slot_name = CUDAPlugin.slot_types[0][0]
        device_alloc = {
            allocated_slot_name: {DeviceId("GPU-1"): Decimal(1)},
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert [dev["device_id"] for dev in attached] == [DeviceId("GPU-1")]

    async def test_returns_every_allocated_device(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """All devices allocated under the slot should be reported."""
        device_alloc = {
            SlotName("cuda.device"): {
                DeviceId("GPU-0"): Decimal(1),
                DeviceId("GPU-1"): Decimal(1),
            },
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert [dev["device_id"] for dev in attached] == [DeviceId("GPU-0"), DeviceId("GPU-1")]

    async def test_unallocated_devices_are_excluded(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """A device present on the host but not allocated must not be reported."""
        device_alloc = {
            SlotName("cuda.device"): {DeviceId("GPU-0"): Decimal(1)},
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert DeviceId("GPU-1") not in [dev["device_id"] for dev in attached]

    async def test_empty_allocation_returns_no_devices(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """An allocation carrying no CUDA slot yields an empty result."""
        attached = await cuda_plugin.get_attached_devices({})

        assert attached == []

    async def test_unknown_device_id_is_ignored(
        self,
        cuda_plugin: CUDAPlugin,
    ) -> None:
        """An allocated id with no matching host device must be skipped, not raise."""
        device_alloc = {
            SlotName("cuda.device"): {DeviceId("GPU-does-not-exist"): Decimal(1)},
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert attached == []
