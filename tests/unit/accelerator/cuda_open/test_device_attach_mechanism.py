from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.accelerator.cuda_open.plugin import (
    CDIAttachMechanism,
    CUDADevice,
    CUDAPlugin,
    EngineVersion,
    LegacyRuntimeAttachMechanism,
    NvidiaDriverAttachMechanism,
)
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


class TestDetectAttachMechanism:
    """Tests for picking the device attach mechanism from the container engine."""

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
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("5.4.0", with_nvidia_runtime=False),
            _version_info(("Podman Engine", "5.4.0")),
        )
        assert isinstance(mechanism, CDIAttachMechanism)

    def test_podman_does_not_require_the_nvidia_runtime(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        # Podman selects its OCI runtime from its own configuration, so the nvidia runtime
        # being absent from the reported runtimes must not disable the plugin.
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("5.8.4", with_nvidia_runtime=False),
            _version_info(("Podman Engine", "5.8.4")),
        )
        assert isinstance(mechanism, CDIAttachMechanism)

    def test_podman_below_the_minimum_version_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("4.9.3"),
            _version_info(("Podman Engine", "4.9.3"), ("Conmon", "conmon version 2.1.10")),
        )
        assert mechanism is None

    def test_podman_without_a_cdi_spec_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_missing: None
    ) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("5.4.0"),
            _version_info(("Podman Engine", "5.4.0")),
        )
        assert mechanism is None

    def test_docker_above_the_device_request_version_uses_the_nvidia_driver(
        self, plugin: CUDAPlugin
    ) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("28.1.1"),
            _version_info(("Engine", "28.1.1")),
        )
        assert isinstance(mechanism, NvidiaDriverAttachMechanism)

    def test_docker_below_the_device_request_version_uses_the_legacy_runtime(
        self, plugin: CUDAPlugin
    ) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("18.9.0"),
            _version_info(("Engine", "18.9.0")),
        )
        assert isinstance(mechanism, LegacyRuntimeAttachMechanism)

    def test_docker_without_the_nvidia_runtime_is_rejected(self, plugin: CUDAPlugin) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("28.1.1", with_nvidia_runtime=False),
            _version_info(("Engine", "28.1.1")),
        )
        assert mechanism is None

    def test_a_cdi_only_engine_with_an_unparsable_version_is_rejected(
        self, plugin: CUDAPlugin, cdi_spec_available: None
    ) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("5.4.0"),
            _version_info(("Podman Engine", "unknown")),
        )
        assert mechanism is None

    def test_an_unparsable_docker_version_is_rejected(self, plugin: CUDAPlugin) -> None:
        mechanism = plugin._detect_attach_mechanism(
            _docker_info("unknown"),
            _version_info(("Engine", "unknown")),
        )
        assert mechanism is None


def _alloc(*device_ids: str) -> dict[SlotName, dict[DeviceId, Decimal]]:
    return {SlotName("cuda.device"): {DeviceId(device_id): Decimal(1) for device_id in device_ids}}


class TestCDIAttachMechanism:
    @pytest.fixture
    def devices(self) -> list[CUDADevice]:
        return [
            _make_device("0", DEVICE_0_UUID),
            _make_device("1", DEVICE_1_UUID),
        ]

    def test_names_devices_by_uuid(self, devices: list[CUDADevice]) -> None:
        # The alloc map keys devices by the CUDA runtime index, which is not guaranteed to
        # match the index CDI assigns, so the UUID is what must reach the engine.
        device_config = CDIAttachMechanism().build_device_config(_alloc("1"), devices)
        assert device_config == {
            "HostConfig": {
                "DeviceRequests": [
                    {"Driver": "cdi", "DeviceIDs": [f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}"]},
                ],
            },
        }

    def test_names_every_allocated_device(self, devices: list[CUDADevice]) -> None:
        device_config = CDIAttachMechanism().build_device_config(_alloc("0", "1"), devices)
        assert device_config["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [
            f"nvidia.com/gpu=GPU-{DEVICE_0_UUID}",
            f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}",
        ]

    def test_omits_the_legacy_runtime_fields(self, devices: list[CUDADevice]) -> None:
        device_config = CDIAttachMechanism().build_device_config(_alloc("0"), devices)
        assert "Env" not in device_config
        assert "Runtime" not in device_config["HostConfig"]

    def test_skips_devices_without_an_allocation(self, devices: list[CUDADevice]) -> None:
        device_alloc = {
            SlotName("cuda.device"): {DeviceId("0"): Decimal(0), DeviceId("1"): Decimal(1)},
        }
        device_config = CDIAttachMechanism().build_device_config(device_alloc, devices)
        assert device_config["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [
            f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}",
        ]

    def test_emits_nothing_for_an_empty_allocation(self, devices: list[CUDADevice]) -> None:
        assert CDIAttachMechanism().build_device_config({}, devices) == {}

    def test_rejects_an_allocation_of_an_unknown_device(self, devices: list[CUDADevice]) -> None:
        # Skipping the device would charge the slot while the container runs without a GPU.
        with pytest.raises(InvalidResourceArgument):
            CDIAttachMechanism().build_device_config(_alloc("7"), devices)


class TestNvidiaDriverAttachMechanism:
    def test_names_devices_by_the_runtime_index(self) -> None:
        device_config = NvidiaDriverAttachMechanism().build_device_config(_alloc("0"), [])
        device_request = device_config["HostConfig"]["DeviceRequests"][0]
        assert device_request["Driver"] == "nvidia"
        assert device_request["DeviceIDs"] == ["0"]

    def test_emits_nothing_for_an_empty_allocation(self) -> None:
        assert NvidiaDriverAttachMechanism().build_device_config({}, []) == {}


class TestLegacyRuntimeAttachMechanism:
    def test_selects_the_nvidia_runtime_and_lists_devices_in_the_environment(self) -> None:
        device_config = LegacyRuntimeAttachMechanism().build_device_config(_alloc("0", "1"), [])
        assert device_config["HostConfig"]["Runtime"] == "nvidia"
        assert "NVIDIA_VISIBLE_DEVICES=0,1" in device_config["Env"]

    def test_still_selects_the_nvidia_runtime_for_an_empty_allocation(self) -> None:
        device_config = LegacyRuntimeAttachMechanism().build_device_config({}, [])
        assert device_config["HostConfig"]["Runtime"] == "nvidia"
        assert "NVIDIA_VISIBLE_DEVICES=" in device_config["Env"]


class TestGenerateDockerArgs:
    """Tests for the plugin delegating to the mechanism it detected."""

    @pytest.fixture
    def cuda_plugin(self) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.plugin_config = {}
        plugin.local_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        plugin._attach_mechanism = CDIAttachMechanism()
        plugin.list_devices = AsyncMock(  # type: ignore[method-assign]
            return_value=[_make_device("0", DEVICE_0_UUID), _make_device("1", DEVICE_1_UUID)],
        )
        return plugin

    async def test_passes_the_allocation_and_the_devices_to_the_mechanism(
        self, cuda_plugin: CUDAPlugin
    ) -> None:
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _alloc("1"))
        assert docker_args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [
            f"nvidia.com/gpu=GPU-{DEVICE_1_UUID}",
        ]

    async def test_a_disabled_plugin_emits_nothing(self, cuda_plugin: CUDAPlugin) -> None:
        cuda_plugin.enabled = False
        docker_args = await cuda_plugin.generate_docker_args(AsyncMock(), _alloc("0"))
        assert docker_args == {}
        cuda_plugin.list_devices.assert_not_awaited()  # type: ignore[attr-defined]
