from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.accelerator.cuda_open.plugin import (
    CDIInjector,
    CUDADevice,
    CUDAPlugin,
    DeviceConfig,
    DeviceRequest,
    EngineVersion,
    HostConfig,
    LegacyRuntimeInjector,
    NvidiaDriverInjector,
)
from ai.backend.agent.data.device import DeviceAllocation
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.common.types import DeviceId, DeviceName, SlotName

DEVICE_0_UUID = "1e826af4-30db-8336-d74d-c958d38334d7"
DEVICE_1_UUID = "8d1f2c05-9a44-4b17-b2e6-6f0a3c7d9e11"


def _make_device(device_id: str, device_uuid: str) -> CUDADevice:
    return CUDADevice(
        device_id=DeviceId(device_id),
        device_name=DeviceName("cuda"),
        model_name="NVIDIA A100",
        uuid=device_uuid,
        hw_location="0000:00:1e.0",
        numa_node=0,
        memory_size=1024 * 1024 * 1024 * 8,
        processing_units=64,
    )


def _version_info(*components: tuple[str, str]) -> EngineVersion:
    return EngineVersion.model_validate({
        "Components": [{"Name": name, "Version": version} for name, version in components],
    })


def _docker_info(server_version: str, *, with_nvidia_runtime: bool = True) -> dict[str, Any]:
    runtimes: dict[str, Any] = {"runc": {}}
    if with_nvidia_runtime:
        runtimes["nvidia"] = {}
    return {"Runtimes": runtimes, "ServerVersion": server_version}


class TestDetectDeviceInjector:
    """Tests for picking the device injector from the container engine."""

    @pytest.fixture
    def plugin(self) -> CUDAPlugin:
        return CUDAPlugin.__new__(CUDAPlugin)

    @pytest.fixture
    def cdi_spec_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(CUDAPlugin, "_has_cdi_spec", lambda self: True)

    @pytest.fixture
    def cdi_spec_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(CUDAPlugin, "_has_cdi_spec", lambda self: False)

    def test_podman_at_the_minimum_version_uses_cdi(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("5.4.0", with_nvidia_runtime=False),
            _version_info(("Podman Engine", "5.4.0")),
        )
        assert isinstance(mechanism, CDIInjector)

    def test_podman_does_not_require_the_nvidia_runtime(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        # Podman selects its OCI runtime from its own configuration, so the nvidia runtime
        # being absent from the reported runtimes must not disable the plugin.
        mechanism = plugin._detect_device_injector(
            _docker_info("5.8.4", with_nvidia_runtime=False),
            _version_info(("Podman Engine", "5.8.4")),
        )
        assert isinstance(mechanism, CDIInjector)

    def test_podman_below_the_minimum_version_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("4.9.3"),
            _version_info(("Podman Engine", "4.9.3"), ("Conmon", "conmon version 2.1.10")),
        )
        assert mechanism is None

    def test_podman_without_a_cdi_spec_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_missing: None
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("5.4.0"),
            _version_info(("Podman Engine", "5.4.0")),
        )
        assert mechanism is None

    def test_docker_above_the_device_request_version_uses_the_nvidia_driver(
        self, plugin: CUDAPlugin
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("28.1.1"),
            _version_info(("Engine", "28.1.1")),
        )
        assert isinstance(mechanism, NvidiaDriverInjector)

    def test_docker_below_the_device_request_version_uses_the_legacy_runtime(
        self, plugin: CUDAPlugin
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("18.9.0"),
            _version_info(("Engine", "18.9.0")),
        )
        assert isinstance(mechanism, LegacyRuntimeInjector)

    def test_docker_without_the_nvidia_runtime_is_rejected(self, plugin: CUDAPlugin) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("28.1.1", with_nvidia_runtime=False),
            _version_info(("Engine", "28.1.1")),
        )
        assert mechanism is None

    def test_a_cdi_only_engine_with_an_unparsable_version_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("5.4.0"),
            _version_info(("Podman Engine", "unknown")),
        )
        assert mechanism is None

    def test_an_unparsable_docker_version_is_rejected(self, plugin: CUDAPlugin) -> None:
        mechanism = plugin._detect_device_injector(
            _docker_info("unknown"),
            _version_info(("Engine", "unknown")),
        )
        assert mechanism is None


def _device_alloc(*device_ids: str) -> dict[SlotName, dict[DeviceId, Decimal]]:
    """The resource-spec form the agent hands to the plugin."""
    return {SlotName("cuda.device"): {DeviceId(device_id): Decimal(1) for device_id in device_ids}}


def _alloc(*device_ids: str) -> DeviceAllocation:
    """The transposed form a mechanism receives."""
    return DeviceAllocation.from_device_alloc(_device_alloc(*device_ids))


class TestCDIInjector:
    @pytest.fixture
    def devices(self) -> list[CUDADevice]:
        return [
            _make_device("0", DEVICE_0_UUID),
            _make_device("1", DEVICE_1_UUID),
        ]

    def test_names_devices_by_uuid(self, devices: list[CUDADevice]) -> None:
        # The alloc map keys devices by the CUDA runtime index, which is not guaranteed to
        # match the index CDI assigns, so the UUID is what must reach the engine.
        device_config = CDIInjector().build_device_config(_alloc("1"), devices)
        assert device_config == DeviceConfig(
            host_config=HostConfig(
                device_requests=[
                    DeviceRequest(
                        driver="cdi",
                        device_ids=[f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}"],
                    ),
                ],
            ),
        )

    def test_names_every_allocated_device(self, devices: list[CUDADevice]) -> None:
        device_config = CDIInjector().build_device_config(_alloc("0", "1"), devices)
        assert device_config == DeviceConfig(
            host_config=HostConfig(
                device_requests=[
                    DeviceRequest(
                        driver="cdi",
                        device_ids=[
                            f"nvidia.com/gpu=GPU-{DEVICE_0_UUID}",
                            f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}",
                        ],
                    ),
                ],
            ),
        )

    def test_skips_devices_without_an_allocation(self, devices: list[CUDADevice]) -> None:
        allocation = DeviceAllocation.from_device_alloc({
            SlotName("cuda.device"): {DeviceId("0"): Decimal(0), DeviceId("1"): Decimal(1)},
        })
        device_config = CDIInjector().build_device_config(allocation, devices)
        assert device_config == DeviceConfig(
            host_config=HostConfig(
                device_requests=[
                    DeviceRequest(
                        driver="cdi",
                        device_ids=[f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}"],
                    ),
                ],
            ),
        )

    def test_requests_nothing_for_an_empty_allocation(self, devices: list[CUDADevice]) -> None:
        assert CDIInjector().build_device_config(_alloc(), devices) == DeviceConfig()

    def test_rejects_an_allocation_of_an_unknown_device(self, devices: list[CUDADevice]) -> None:
        # Skipping the device would charge the slot while the container runs without a GPU.
        with pytest.raises(InvalidResourceArgument):
            CDIInjector().build_device_config(_alloc("7"), devices)


class TestNvidiaDriverInjector:
    def test_names_devices_by_the_runtime_index(self) -> None:
        device_config = NvidiaDriverInjector().build_device_config(_alloc("0"), [])
        assert device_config == DeviceConfig(
            host_config=HostConfig(
                device_requests=[
                    DeviceRequest(
                        driver="nvidia",
                        device_ids=["0"],
                        capabilities=[["utility", "compute", "video", "graphics", "display"]],
                    ),
                ],
            ),
        )

    def test_requests_nothing_for_an_empty_allocation(self) -> None:
        assert NvidiaDriverInjector().build_device_config(_alloc(), []) == DeviceConfig()


class TestLegacyRuntimeInjector:
    def test_selects_the_nvidia_runtime_and_lists_devices_in_the_environment(self) -> None:
        device_config = LegacyRuntimeInjector().build_device_config(_alloc("0", "1"), [])
        assert device_config == DeviceConfig(
            host_config=HostConfig(runtime="nvidia"),
            environ=[
                "NVIDIA_DRIVER_CAPABILITIES=all",
                "NVIDIA_VISIBLE_DEVICES=0,1",
            ],
        )

    def test_still_selects_the_nvidia_runtime_for_an_empty_allocation(self) -> None:
        device_config = LegacyRuntimeInjector().build_device_config(_alloc(), [])
        assert device_config.host_config == HostConfig(runtime="nvidia")


class TestGenerateDockerArgs:
    """Tests for rendering an injector's output into the container creation API's keys."""

    @pytest.fixture
    def cuda_plugin(self) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.plugin_config = {}
        plugin.local_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        plugin._device_injector = CDIInjector()
        plugin.list_devices = AsyncMock(  # type: ignore[method-assign]
            return_value=[_make_device("0", DEVICE_0_UUID), _make_device("1", DEVICE_1_UUID)],
        )
        return plugin

    async def test_renders_a_device_request(self, cuda_plugin: CUDAPlugin) -> None:
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _device_alloc("1"))
        assert docker_args == {
            "HostConfig": {
                "DeviceRequests": [
                    {
                        "Driver": "cdi",
                        "DeviceIDs": [f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}"],
                    },
                ],
            },
        }

    async def test_renders_the_capabilities_only_when_the_request_carries_them(
        self, cuda_plugin: CUDAPlugin
    ) -> None:
        cuda_plugin._device_injector = NvidiaDriverInjector()
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _device_alloc("0"))
        assert docker_args == {
            "HostConfig": {
                "DeviceRequests": [
                    {
                        "Driver": "nvidia",
                        "DeviceIDs": ["0"],
                        "Capabilities": [
                            ["utility", "compute", "video", "graphics", "display"],
                        ],
                    },
                ],
            },
        }

    async def test_renders_the_runtime_and_the_environment(self, cuda_plugin: CUDAPlugin) -> None:
        cuda_plugin._device_injector = LegacyRuntimeInjector()
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _device_alloc("0"))
        assert docker_args == {
            "HostConfig": {"Runtime": "nvidia"},
            "Env": [
                "NVIDIA_DRIVER_CAPABILITIES=all",
                "NVIDIA_VISIBLE_DEVICES=0",
            ],
        }

    async def test_renders_nothing_for_an_empty_device_config(
        self, cuda_plugin: CUDAPlugin
    ) -> None:
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), {})
        assert docker_args == {}

    async def test_a_disabled_plugin_emits_nothing(self, cuda_plugin: CUDAPlugin) -> None:
        cuda_plugin.enabled = False
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _device_alloc("0"))
        assert docker_args == {}
        cuda_plugin.list_devices.assert_not_awaited()  # type: ignore[attr-defined]
