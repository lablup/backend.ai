from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from ai.backend.accelerator.cuda_open.plugin import CUDAPlugin
from ai.backend.common.types import DeviceId, SlotName


@dataclass
class FakeCUDADevice:
    device_id: DeviceId
    processing_units: int
    memory_size: int
    model_name: str


class TestGetAttachedDevices:
    """Regression: ``get_attached_devices`` must read the ``cuda.device`` (singular) slot.

    The allocation the agent passes in is keyed by ``SlotName("cuda.device")`` — the slot the
    plugin registers everywhere else. A stale ``cuda.devices`` (plural) lookup matched nothing,
    so the attached-device list came back empty and the agent's GPU convention env-vars
    (``GPU_COUNT`` / ``N_GPUS`` / ``GPU_MODEL_NAME`` / ``GPU_CONFIG``) were 0/absent even though a
    GPU was attached — device *injection* uses a separate, slot-name-agnostic path, so the
    breakage was silent.
    """

    @pytest.fixture
    def cuda_plugin(self) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.enabled = True
        return plugin

    @pytest.fixture
    def fake_devices(self) -> list[FakeCUDADevice]:
        return [
            FakeCUDADevice(DeviceId("GPU-0"), 128, 8 * 1024**3, "NVIDIA Test GPU"),
            FakeCUDADevice(DeviceId("GPU-1"), 128, 8 * 1024**3, "NVIDIA Test GPU"),
        ]

    async def test_returns_attached_device_for_cuda_device_slot(
        self, cuda_plugin: CUDAPlugin, fake_devices: list[FakeCUDADevice]
    ) -> None:
        """A ``cuda.device`` allocation yields the matching attached device with its metadata."""
        cuda_plugin.list_devices = AsyncMock(return_value=fake_devices)  # type: ignore[method-assign]
        device_alloc = {SlotName("cuda.device"): {DeviceId("GPU-0"): Decimal(1)}}

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert [d["device_id"] for d in attached] == [DeviceId("GPU-0")]
        assert attached[0]["model_name"] == "NVIDIA Test GPU"
        assert attached[0]["data"]["mem"] == 8 * 1024**3

    async def test_returns_all_allocated_devices(
        self, cuda_plugin: CUDAPlugin, fake_devices: list[FakeCUDADevice]
    ) -> None:
        """Every device in the ``cuda.device`` allocation is reported."""
        cuda_plugin.list_devices = AsyncMock(return_value=fake_devices)  # type: ignore[method-assign]
        device_alloc = {
            SlotName("cuda.device"): {DeviceId("GPU-0"): Decimal(1), DeviceId("GPU-1"): Decimal(1)}
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert {d["device_id"] for d in attached} == {DeviceId("GPU-0"), DeviceId("GPU-1")}

    async def test_empty_when_no_cuda_device_slot(
        self, cuda_plugin: CUDAPlugin, fake_devices: list[FakeCUDADevice]
    ) -> None:
        """An allocation without the ``cuda.device`` slot attaches nothing."""
        cuda_plugin.list_devices = AsyncMock(return_value=fake_devices)  # type: ignore[method-assign]
        device_alloc: dict[SlotName, dict[DeviceId, Decimal]] = {
            SlotName("cpu"): {DeviceId("0"): Decimal(1)}
        }

        attached = await cuda_plugin.get_attached_devices(device_alloc)

        assert attached == []
