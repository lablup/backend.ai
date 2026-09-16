import logging
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.accelerator.dax.plugin import DAXPlugin
from ai.backend.agent.alloc_map import AbstractAllocMap
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import Container
from ai.backend.common.types import (
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ResourceSlot,
    SlotName,
)

from .conftest import FakeSysfs, PluginFactory

SLOT = SlotName("dax.device")
DEV_A = DeviceId("dax-0x1a2b")
DEV_B = DeviceId("dax-0x3c4d")
GONE = DeviceId("dax-0xdead")
SPEC_FUNC = "ai.backend.accelerator.dax.plugin.get_resource_spec_from_container"


def _spec(
    allocations: Mapping[DeviceName, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
) -> KernelResourceSpec:
    return KernelResourceSpec(
        slots=ResourceSlot(), allocations=dict(allocations), scratch_disk_size=0
    )


def _dax_spec(*device_ids: DeviceId) -> KernelResourceSpec:
    return _spec({DeviceName("dax"): {SLOT: {device_id: Decimal(1) for device_id in device_ids}}})


def _container(backend_obj: Any) -> Container:
    return Container(
        id=ContainerId("c0ffee"),
        status=ContainerStatus.RUNNING,
        image="python:3.13",
        labels={},
        ports=[],
        backend_obj=backend_obj,
    )


def _mounted(*paths: str) -> dict[str, Any]:
    return {
        "HostConfig": {
            "Devices": [
                {"PathOnHost": f"/host{p}", "PathInContainer": p, "CgroupPermissions": "rw"}
                for p in paths
            ]
        }
    }


def _held(alloc_map: AbstractAllocMap) -> dict[DeviceId, Decimal]:
    return {dev: amount for dev, amount in alloc_map.allocations[SLOT].items() if amount > 0}


@pytest.fixture
async def plugin(fake_sysfs: FakeSysfs, plugin_factory: PluginFactory) -> DAXPlugin:
    # After the reboot: 0x1a2b is at dax0.0 and 0x3c4d is at dax1.0.
    fake_sysfs.add_cxl_device("dax0.0", serials=("0x1a2b",))
    fake_sysfs.add_cxl_device("dax1.0", region="region1", serials=("0x3c4d",))
    return await plugin_factory()


@pytest.fixture
async def alloc_map(plugin: DAXPlugin) -> AbstractAllocMap:
    return await plugin.create_alloc_map()


@pytest.fixture
def spec_mock() -> Iterator[AsyncMock]:
    with patch(SPEC_FUNC, new_callable=AsyncMock) as mock:
        yield mock


class TestRestoreMatching:
    async def test_same_id_at_same_path_is_held(
        self, plugin: DAXPlugin, alloc_map: AbstractAllocMap, spec_mock: AsyncMock
    ) -> None:
        spec_mock.return_value = _dax_spec(DEV_A)

        await plugin.restore_from_container(_container(_mounted("/dev/dax0.0")), alloc_map)

        assert _held(alloc_map) == {DEV_A: Decimal(1)}

    async def test_same_serial_at_new_path_holds_both(
        self,
        plugin: DAXPlugin,
        alloc_map: AbstractAllocMap,
        spec_mock: AsyncMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        spec_mock.return_value = _dax_spec(DEV_A)

        with caplog.at_level(logging.ERROR):
            await plugin.restore_from_container(_container(_mounted("/dev/dax1.0")), alloc_map)

        assert _held(alloc_map) == {DEV_A: Decimal(1), DEV_B: Decimal(1)}
        assert "identity_mismatch" in caplog.text
        assert DEV_A in caplog.text
        assert DEV_B in caplog.text

    async def test_gone_id_holds_device_now_at_its_path(
        self,
        plugin: DAXPlugin,
        alloc_map: AbstractAllocMap,
        spec_mock: AsyncMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        spec_mock.return_value = _dax_spec(GONE)

        with caplog.at_level(logging.ERROR):
            await plugin.restore_from_container(_container(_mounted("/dev/dax0.0")), alloc_map)

        assert _held(alloc_map) == {DEV_A: Decimal(1)}
        assert GONE not in alloc_map.allocations[SLOT]
        assert "identity_mismatch" in caplog.text


class TestRestoreEdges:
    async def test_id_and_path_both_gone_holds_nothing(
        self, plugin: DAXPlugin, alloc_map: AbstractAllocMap, spec_mock: AsyncMock
    ) -> None:
        spec_mock.return_value = _dax_spec(GONE)

        await plugin.restore_from_container(_container(_mounted("/dev/dax9.0")), alloc_map)

        assert _held(alloc_map) == {}
        assert GONE not in alloc_map.allocations[SLOT]

    @pytest.mark.parametrize(
        "spec",
        [
            pytest.param(None, id="no-config-mount"),
            pytest.param(_spec({}), id="no-dax-line"),
        ],
    )
    async def test_no_dax_record_is_noop(
        self,
        plugin: DAXPlugin,
        alloc_map: AbstractAllocMap,
        spec_mock: AsyncMock,
        spec: KernelResourceSpec | None,
    ) -> None:
        spec_mock.return_value = spec

        await plugin.restore_from_container(_container(_mounted("/dev/dax0.0")), alloc_map)

        assert _held(alloc_map) == {}

    @pytest.mark.parametrize(
        "backend_obj",
        [
            pytest.param({"HostConfig": {"Devices": [{"Bogus": 1}]}}, id="device-without-path"),
            pytest.param({"HostConfig": {"Devices": 42}}, id="devices-not-a-list"),
            pytest.param("not-a-mapping", id="not-a-mapping"),
        ],
    )
    async def test_malformed_container_does_not_raise(
        self,
        plugin: DAXPlugin,
        alloc_map: AbstractAllocMap,
        spec_mock: AsyncMock,
        backend_obj: Any,
    ) -> None:
        spec_mock.return_value = _dax_spec(DEV_A)

        await plugin.restore_from_container(_container(backend_obj), alloc_map)

    async def test_malformed_resource_spec_does_not_raise(
        self, plugin: DAXPlugin, alloc_map: AbstractAllocMap, spec_mock: AsyncMock
    ) -> None:
        spec_mock.side_effect = ValueError("broken resource.txt")

        await plugin.restore_from_container(_container(_mounted("/dev/dax0.0")), alloc_map)

        assert _held(alloc_map) == {}

    async def test_missing_resource_file_is_reraised(
        self, plugin: DAXPlugin, alloc_map: AbstractAllocMap, spec_mock: AsyncMock
    ) -> None:
        spec_mock.side_effect = FileNotFoundError("resource.txt")

        with pytest.raises(FileNotFoundError):
            await plugin.restore_from_container(_container(_mounted("/dev/dax0.0")), alloc_map)
