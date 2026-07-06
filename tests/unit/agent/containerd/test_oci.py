from typing import Any, cast

from pathlib import Path

from ai.backend.agent.containerd.oci import (
    KERNEL_ID_LABEL,
    KRUNNER_ENTRYPOINT,
    SESSION_ID_LABEL,
    mount_to_oci,
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
            Mount(MountTypes.BIND, Path("/host/su-exec"), Path("/opt/kernel/su-exec"),
                  MountPermission.READ_ONLY),
            Mount(MountTypes.BIND, Path("/host/work"), Path("/home/work"),
                  MountPermission.READ_WRITE),
        ]
        spec = translate_creation_config(_kernel_config(), environ={}, mounts=mounts)
        oci_mounts = {m["destination"]: m for m in spec.oci_spec["mounts"]}
        assert oci_mounts["/opt/kernel/su-exec"]["source"] == "/host/su-exec"
        assert oci_mounts["/opt/kernel/su-exec"]["readonly"] is True
        assert oci_mounts["/home/work"]["readonly"] is False

    def test_mounts_sorted_parent_before_child(self) -> None:
        # parent (/opt/backend.ai) must precede nested (/opt/backend.ai/lib/.../kernel)
        mounts = [
            Mount(MountTypes.BIND, Path("/h/k"), Path("/opt/backend.ai/lib/py/kernel"),
                  MountPermission.READ_ONLY),
            Mount(MountTypes.VOLUME, Path("krunner-vol"), Path("/opt/backend.ai"),
                  MountPermission.READ_WRITE),
        ]
        spec = translate_creation_config(_kernel_config(), environ={}, mounts=mounts)
        dests = [m["destination"] for m in spec.oci_spec["mounts"]]
        assert dests.index("/opt/backend.ai") < dests.index("/opt/backend.ai/lib/py/kernel")


class TestMountToOci:
    def test_readonly_flag(self) -> None:
        ro = mount_to_oci(Mount(MountTypes.BIND, Path("/a"), Path("/b"), MountPermission.READ_ONLY))
        rw = mount_to_oci(Mount(MountTypes.BIND, Path("/a"), Path("/b"), MountPermission.READ_WRITE))
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
