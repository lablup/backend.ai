"""Tests for ModelServiceProvisioner with model definitions from Manager."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.exception import InvalidModelConfigurationError
from ai.backend.agent.stage.kernel_lifecycle.docker.model_service import (
    ModelServiceProvisioner,
    ModelServiceSpec,
)
from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import (
    RuntimeVariant,
    SessionTypes,
    VFolderMount,
)


def _make_vfolder_mount() -> VFolderMount:
    mock = MagicMock(spec=VFolderMount)
    mock.name = "test-model"
    mock.kernel_path = MagicMock()
    mock.kernel_path.as_posix.return_value = "/models"
    mock.host_path = MagicMock()
    return mock


def _make_model_definition_dict(
    initial_delay: float = 300,
    max_retries: int = 30,
    max_wait_time: float = 20,
) -> dict[str, Any]:
    return {
        "models": [
            {
                "name": "vllm-model",
                "model_path": "/models",
                "service": {
                    "start_command": "vllm serve",
                    "port": 8000,
                    "health_check": {
                        "path": "/health",
                        "initial_delay": initial_delay,
                        "max_retries": max_retries,
                        "max_wait_time": max_wait_time,
                    },
                },
            }
        ]
    }


class TestModelServiceProvisionerGetModelDefinition:
    """Tests for ModelServiceProvisioner._get_model_definition()."""

    def test_uses_model_definition_from_spec(self) -> None:
        """When spec.model_definition is set, it should be validated and returned."""
        model_definition_dict = _make_model_definition_dict(
            initial_delay=300, max_retries=30, max_wait_time=20
        )
        spec = ModelServiceSpec(
            session_type=SessionTypes.INFERENCE,
            model_vfolder_mount=_make_vfolder_mount(),
            runtime_variant=RuntimeVariant("vllm"),
            model_definition=model_definition_dict,
            image_command="vllm serve",
        )

        provisioner = ModelServiceProvisioner()
        result = provisioner._get_model_definition(spec)

        assert isinstance(result, ModelDefinition)
        assert len(result.models) == 1
        model = result.models[0]
        assert model.name == "vllm-model"
        assert model.service is not None
        assert model.service.health_check is not None
        assert model.service.health_check.initial_delay == 300
        assert model.service.health_check.max_retries == 30
        assert model.service.health_check.max_wait_time == 20

    def test_raises_error_when_model_definition_absent(self) -> None:
        """When spec.model_definition is None, raise InvalidModelConfigurationError."""
        spec = ModelServiceSpec(
            session_type=SessionTypes.INFERENCE,
            model_vfolder_mount=_make_vfolder_mount(),
            runtime_variant=RuntimeVariant("vllm"),
            model_definition=None,
            image_command="vllm serve",
        )

        provisioner = ModelServiceProvisioner()
        with pytest.raises(InvalidModelConfigurationError):
            provisioner._get_model_definition(spec)

    def test_preserves_all_health_check_fields(self) -> None:
        """All health_check fields from model definition should be preserved."""
        model_definition_dict = {
            "models": [
                {
                    "name": "test-model",
                    "model_path": "/models",
                    "service": {
                        "start_command": "serve",
                        "port": 9000,
                        "health_check": {
                            "path": "/v1/health",
                            "interval": 5,
                            "initial_delay": 600,
                            "max_retries": 60,
                            "max_wait_time": 30,
                            "expected_status_code": 200,
                        },
                    },
                }
            ]
        }
        spec = ModelServiceSpec(
            session_type=SessionTypes.INFERENCE,
            model_vfolder_mount=_make_vfolder_mount(),
            runtime_variant=RuntimeVariant("vllm"),
            model_definition=model_definition_dict,
            image_command="serve",
        )

        provisioner = ModelServiceProvisioner()
        result = provisioner._get_model_definition(spec)

        service = result.models[0].service
        assert service is not None
        health_check = service.health_check
        assert health_check is not None
        assert health_check.path == "/v1/health"
        assert health_check.interval == 5
        assert health_check.initial_delay == 600
        assert health_check.max_retries == 60
        assert health_check.max_wait_time == 30
        assert health_check.expected_status_code == 200
