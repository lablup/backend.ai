from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.oci import (
    KERNEL_ID_LABEL,
    KRUNNER_ENTRYPOINT,
    SESSION_ID_LABEL,
    DevicePassthrough,
    infiniband_devices,
    mount_to_oci,
    translate_accelerator_args,
    translate_creation_config,
)
from ai.backend.agent.resources import Mount
from ai.backend.common.types import KernelCreationConfig, MountPermission, MountTypes


def _kernel_config(**over: Any) -> KernelCreationConfig:
    base: dict[str, Any] = {
        "image": {"canonical": "cr.backend.ai/stable/python:3.10", "labels": {}},
        "kernel_id": "kern-123",
        "session_id": "sess-abc",
        "network_id": "net-1",
    }
    base.update(over)
    return cast(KernelCreationConfig, base)


class TestTranslateCreationConfig:
    def test_maps_ids_and_image(self) -> None:
        spec = translate_creation_config(_kernel_config(), environ={"FOO": "bar"})
        assert spec.container_id == "kern-123"  # container id = kernel id
        assert spec.session_id == "sess-abc"
        assert spec.image_ref == "cr.backend.ai/stable/python:3.10"
        assert spec.command == [KRUNNER_ENTRYPOINT]  # default = krunner entrypoint

    def test_injects_mounts(self) -> None:
        mounts = [
            Mount(
                MountTypes.BIND,
                Path("/host/su-exec"),
                Path("/opt/kernel/su-exec"),
                MountPermission.READ_ONLY,
            ),
            Mount(
                MountTypes.BIND, Path("/host/work"), Path("/home/work"), MountPermission.READ_WRITE
            ),
        ]
        spec = translate_creation_config(_kernel_config(), environ={}, mounts=mounts)
        oci_mounts = {m["destination"]: m for m in spec.oci_spec["mounts"]}
        assert oci_mounts["/opt/kernel/su-exec"]["source"] == "/host/su-exec"
        assert oci_mounts["/opt/kernel/su-exec"]["readonly"] is True
        assert oci_mounts["/home/work"]["readonly"] is False

    def test_mounts_sorted_parent_before_child(self) -> None:
        # parent (/opt/backend.ai) must precede nested (/opt/backend.ai/lib/.../kernel)
        mounts = [
            Mount(
                MountTypes.BIND,
                Path("/h/k"),
                Path("/opt/backend.ai/lib/py/kernel"),
                MountPermission.READ_ONLY,
            ),
            Mount(
                MountTypes.VOLUME,
                Path("krunner-vol"),
                Path("/opt/backend.ai"),
                MountPermission.READ_WRITE,
            ),
        ]
        spec = translate_creation_config(_kernel_config(), environ={}, mounts=mounts)
        dests = [m["destination"] for m in spec.oci_spec["mounts"]]
        assert dests.index("/opt/backend.ai") < dests.index("/opt/backend.ai/lib/py/kernel")


class TestMountToOci:
    def test_readonly_flag(self) -> None:
        ro = mount_to_oci(Mount(MountTypes.BIND, Path("/a"), Path("/b"), MountPermission.READ_ONLY))
        rw = mount_to_oci(
            Mount(MountTypes.BIND, Path("/a"), Path("/b"), MountPermission.READ_WRITE)
        )
        assert ro["readonly"] is True and rw["readonly"] is False

    def test_labels_and_env(self) -> None:
        spec = translate_creation_config(_kernel_config(), environ={"A": "1"})
        assert spec.oci_spec["labels"][KERNEL_ID_LABEL] == "kern-123"
        assert spec.oci_spec["labels"][SESSION_ID_LABEL] == "sess-abc"
        assert spec.oci_spec["env"] == {"A": "1"}

    def test_explicit_command_override(self) -> None:
        spec = translate_creation_config(
            _kernel_config(), environ={}, command=["/opt/kernel/entrypoint.sh"]
        )
        assert spec.command == ["/opt/kernel/entrypoint.sh"]


class TestTranslateAcceleratorArgs:
    def test_nvidia_device_requests(self) -> None:
        # cuda_open on modern docker -> DeviceRequests{Driver: nvidia}
        args = {
            "HostConfig": {
                "DeviceRequests": [{"Driver": "nvidia", "DeviceIDs": ["0", "1"]}],
            }
        }
        spec = translate_accelerator_args(args)
        assert spec.gpu_device_ids == ["0", "1"]
        assert spec.devices == []

    def test_nvidia_runtime_env_fallback(self) -> None:
        # older docker path -> Runtime=nvidia + NVIDIA_VISIBLE_DEVICES
        args = {
            "HostConfig": {"Runtime": "nvidia"},
            "Env": ["NVIDIA_DRIVER_CAPABILITIES=all", "NVIDIA_VISIBLE_DEVICES=0,3"],
        }
        spec = translate_accelerator_args(args)
        assert spec.gpu_device_ids == ["0", "3"]
        assert spec.env["NVIDIA_DRIVER_CAPABILITIES"] == "all"

    def test_amd_npu_device_passthrough(self) -> None:
        # ROCm / NPUs -> HostConfig.Devices (/dev node passthrough, no nvidia runtime)
        args = {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": "/dev/dri/renderD128",
                        "PathInContainer": "/dev/dri/renderD128",
                        "CgroupPermissions": "mrw",
                    },
                    {"PathOnHost": "/dev/kfd"},  # PathInContainer defaults to host path
                ]
            }
        }
        spec = translate_accelerator_args(args)
        assert spec.gpu_device_ids == []
        assert spec.devices == [
            DevicePassthrough("/dev/dri/renderD128", "/dev/dri/renderD128", "mrw"),
            DevicePassthrough("/dev/kfd", "/dev/kfd", "rwm"),
        ]

    def test_empty_args_yield_empty_spec(self) -> None:
        spec = translate_accelerator_args({})
        assert spec.devices == [] and spec.gpu_device_ids == [] and spec.env == {}
        assert spec.cpuset_cpus is None and spec.memory_limit is None

    def test_cpu_pinning_extracted(self) -> None:
        # CPUPlugin -> HostConfig{Cpus, CpusetCpus}
        spec = translate_accelerator_args({"HostConfig": {"Cpus": 3, "CpusetCpus": "0,2,4"}})
        assert spec.cpuset_cpus == "0,2,4"

    def test_memory_limits_extracted(self) -> None:
        # MemoryPlugin -> HostConfig{Memory, MemorySwap}
        spec = translate_accelerator_args({
            "HostConfig": {"Memory": 2147483648, "MemorySwap": 2147483648}
        })
        assert spec.memory_limit == 2147483648
        assert spec.memory_swap == 2147483648


class TestInfinibandDevices:
    """Docker-parity RDMA passthrough: enumerate the host's IB char devices when present."""

    def _fake_ib(self, tmp_path: Path, names: list[str], monkeypatch: pytest.MonkeyPatch) -> Path:
        ib = tmp_path / "infiniband"
        ib.mkdir()
        for name in names:
            (ib / name).touch()
        # the host has no real char devices under a tmp dir, so treat the created files as such
        monkeypatch.setattr(
            Path, "is_char_device", lambda self, _n=set(names): self.name in _n, raising=False
        )
        return ib

    def test_no_ib_dir_yields_nothing(self, tmp_path: Path) -> None:
        assert infiniband_devices(tmp_path / "absent") == []

    def test_dir_without_uverbs0_yields_nothing(self, tmp_path: Path) -> None:
        # the uverbs0 sentinel gates the whole passthrough (matches the Docker backend)
        ib = tmp_path / "infiniband"
        ib.mkdir()
        (ib / "rdma_cm").touch()
        assert infiniband_devices(ib) == []

    def test_enumerates_every_char_device(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ib = self._fake_ib(
            tmp_path, ["uverbs0", "uverbs1", "rdma_cm", "issm0", "umad0"], monkeypatch
        )
        devs = infiniband_devices(ib)
        assert [d.source for d in devs] == [
            str(ib / n) for n in ["issm0", "rdma_cm", "umad0", "uverbs0", "uverbs1"]
        ]
        # each is a bidirectional rwm passthrough (source == destination)
        assert all(d.source == d.destination and d.permissions == "rwm" for d in devs)

    def test_non_char_entries_are_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ib = self._fake_ib(tmp_path, ["uverbs0"], monkeypatch)
        (ib / "some-regular-file").touch()  # not a char device -> excluded
        (ib / "subdir").mkdir()  # not a char device -> excluded
        assert [Path(d.source).name for d in infiniband_devices(ib)] == ["uverbs0"]
