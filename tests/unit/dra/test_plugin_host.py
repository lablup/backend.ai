from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.common.types import DeviceId
from ai.backend.dra.errors import UnknownDeviceError, UnsupportedContainerArgsError
from ai.backend.dra.host.isolation import HamiCore
from ai.backend.dra.host.plugin_host import PluginHost, device_name, docker_args_to_edits

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


@pytest.fixture
async def mock_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PluginHost:
    (tmp_path / "mock-accelerator.toml").write_text(MOCK_CONFIG)
    monkeypatch.chdir(tmp_path)
    return await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "discrete"},
        {},
        mount_root=tmp_path / "mounts",
    )


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


class TestDeviceName:
    def test_is_a_dns_label(self) -> None:
        assert device_name(DeviceId("MIG-ABC/1/0")) == "dev-mig-abc-1-0"


class TestPluginHost:
    async def test_lists_mock_devices_with_schema_attributes(self, mock_host: PluginHost) -> None:
        response = await mock_host.list_devices()
        assert response.slot_name == "cuda"
        [first, _] = response.devices
        assert first.attributes["slotName"] == "cuda.device"
        assert first.attributes["numaNode"] == 0
        assert first.capacity["memory"] == str(40 * 1024**3)

    async def test_prepare_returns_the_plugin_injection(self, mock_host: PluginHost) -> None:
        devices = (await mock_host.list_devices()).devices
        edits = await mock_host.prepare("claim-1", [devices[1].name])
        assert "BACKENDAI_MOCK_CUDA_DEVICE_COUNT=1" in edits.env
        assert "BACKENDAI_MOCK_CUDA_DEVICES=aaaaaaaa-0000-0000-0000-000000000002" in edits.env

    async def test_prepare_rejects_unknown_devices(self, mock_host: PluginHost) -> None:
        with pytest.raises(UnknownDeviceError):
            await mock_host.prepare("claim-1", ["dev-nope"])


class TestCDIDeviceRequests:
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


@pytest.fixture
async def shared_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PluginHost:
    (tmp_path / "mock-accelerator.toml").write_text(MOCK_CONFIG)
    monkeypatch.chdir(tmp_path)
    return await PluginHost.start(
        "ai.backend.accelerator.mock.plugin:MockPlugin",
        {"allocation_mode": "discrete"},
        {},
        mount_root=tmp_path / "mounts",
        shared=True,
        isolation=HamiCore(Path("/var/lib/bai-dra/hami-core")),
    )


class TestSharedDevices:
    async def test_devices_carry_a_shares_capacity(self, shared_host: PluginHost) -> None:
        [first, _] = (await shared_host.list_devices()).devices
        assert first.allow_multiple_allocations
        assert first.capacity == {"shares": "100"}
        assert first.attributes["memory"] == 40 * 1024**3
        assert first.request_policies["shares"].default == "100"

    async def test_a_share_is_isolated_by_hami_core(self, shared_host: PluginHost) -> None:
        devices = (await shared_host.list_devices()).devices
        name = devices[0].name
        edits = await shared_host.prepare("claim-1", [name], {name: {"shares": "25"}})
        assert f"CUDA_DEVICE_MEMORY_LIMIT_0={40 * 1024 // 4}m" in edits.env
        assert "CUDA_DEVICE_SM_LIMIT=25" in edits.env
        assert {m.container_path for m in edits.mounts} >= {
            "/usr/local/vgpu/libvgpu.so",
            "/etc/ld.so.preload",
        }

    async def test_a_whole_device_is_not_limited(self, shared_host: PluginHost) -> None:
        name = (await shared_host.list_devices()).devices[0].name
        edits = await shared_host.prepare("claim-1", [name], {})
        assert not any(e.startswith("CUDA_DEVICE_MEMORY_LIMIT") for e in edits.env)
