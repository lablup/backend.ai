from __future__ import annotations

import pytest

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestContainerdConfig:
    def test_connection_defaults(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.address == "/run/containerd/containerd.sock"
        assert config.namespace == "backend-ai"
        assert config.snapshotter == "overlayfs"
        assert config.create_task_timeout == 30.0

    def test_connection_overrides(self) -> None:
        config = ContainerdConfig.model_validate({
            "address": "/run/k3s/containerd/containerd.sock",
            "namespace": "k8s.io",
            "snapshotter": "native",
        })

        assert config.address == "/run/k3s/containerd/containerd.sock"
        assert config.namespace == "k8s.io"
        assert config.snapshotter == "native"

    @pytest.mark.parametrize("key", ["create-task-timeout", "create_task_timeout"])
    def test_create_task_timeout_keys(self, key: str) -> None:
        assert ContainerdConfig.model_validate({key: 120}).create_task_timeout == 120.0

    @pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
    def test_create_task_timeout_must_be_positive_and_finite(self, value: float) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ContainerdConfig.model_validate({"create-task-timeout": value})
