from __future__ import annotations

import pytest

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestContainerdConfig:
    def test_defaults_are_empty(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.runtime_profiles == []
        assert config.profile_required_slots == []
        assert config.profiles == {}

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

    def test_kebab_keys(self) -> None:
        config = ContainerdConfig.model_validate({
            "runtime-profiles": ["coco-tdx"],
            "profile-required-slots": ["confidential.tdx"],
            "create-task-timeout": 1200,
        })

        assert config.runtime_profiles == ["coco-tdx"]
        assert config.profile_required_slots == ["confidential.tdx"]
        assert config.create_task_timeout == 1200.0

    def test_snake_keys(self) -> None:
        config = ContainerdConfig.model_validate({
            "runtime_profiles": ["coco-tdx"],
            "profile_required_slots": ["confidential.tdx"],
            "create_task_timeout": 1200,
        })

        assert config.runtime_profiles == ["coco-tdx"]
        assert config.profile_required_slots == ["confidential.tdx"]
        assert config.create_task_timeout == 1200.0

    @pytest.mark.parametrize("value", [0, -1])
    def test_create_task_timeout_must_be_positive(self, value: int) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ContainerdConfig.model_validate({"create-task-timeout": value})

    def test_profiles_nested_table_is_preserved(self) -> None:
        table = {"coco-tdx": {"standin-image": "ref", "nested": {"k": 1}}}

        config = ContainerdConfig.model_validate({"profiles": table})

        assert config.profiles == table
