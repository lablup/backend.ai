from typing import Any, cast

from ai.backend.agent.containerd.oci import (
    KERNEL_ID_LABEL,
    SESSION_ID_LABEL,
    translate_creation_config,
)
from ai.backend.common.types import KernelCreationConfig


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
        assert spec.command == []  # image default until krunner lands

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
