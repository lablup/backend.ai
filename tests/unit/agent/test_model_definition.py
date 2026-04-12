"""Tests for model definition loading from Manager-provided internal_data."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock
from uuid import UUID

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.agent import ModelDefinitionNotFoundError
from ai.backend.common.types import (
    RuntimeVariant,
    ServicePort,
    VFolderMount,
)


def _make_vfolder_mount(
    name: str = "test-model",
    folder_id: str = "00000000-0000-0000-0000-000000000001",
) -> VFolderMount:
    """Create a minimal VFolderMount for testing."""
    mock = MagicMock(spec=VFolderMount)
    mock.name = name
    mock.vfid = MagicMock()
    mock.vfid.folder_id = UUID(folder_id)
    mock.kernel_path = MagicMock()
    mock.kernel_path.as_posix.return_value = "/models"
    mock.host_path = MagicMock()
    return mock


def _make_model_definition(
    initial_delay: float = 300,
    max_retries: int = 30,
    max_wait_time: float = 20,
) -> dict[str, Any]:
    """Create a model definition dict with custom health_check values."""
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


class TestApplyModelDefinition:
    """Tests for AbstractAgent._apply_model_definition()."""

    def test_applies_custom_health_check_values(self) -> None:
        """Model definition with custom health_check values should be applied correctly."""
        raw_definition = _make_model_definition(
            initial_delay=300,
            max_retries=30,
            max_wait_time=20,
        )
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []

        result = AbstractAgent._apply_model_definition(
            Mock(), raw_definition, model_folder, environ, service_ports
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 300
        assert health_check["max_retries"] == 30
        assert health_check["max_wait_time"] == 20

    def test_sets_environ_variables(self) -> None:
        """Model definition should populate BACKEND_MODEL_NAME and BACKEND_MODEL_PATH."""
        raw_definition = _make_model_definition()
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []

        AbstractAgent._apply_model_definition(
            Mock(), raw_definition, model_folder, environ, service_ports
        )

        assert environ["BACKEND_MODEL_NAME"] == "vllm-model"
        assert environ["BACKEND_MODEL_PATH"] == "/models"

    def test_appends_service_port(self) -> None:
        """Model definition with service config should add a service port."""
        raw_definition = _make_model_definition()
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []

        AbstractAgent._apply_model_definition(
            Mock(), raw_definition, model_folder, environ, service_ports
        )

        assert len(service_ports) == 1
        assert service_ports[0]["container_ports"] == (8000,)
        assert service_ports[0]["is_inference"] is True

    def test_applies_default_health_check_values_when_omitted(self) -> None:
        """Health check fields not specified should get trafaret defaults."""
        raw_definition = {
            "models": [
                {
                    "name": "vllm-model",
                    "model_path": "/models",
                    "service": {
                        "start_command": "vllm serve",
                        "port": 8000,
                        "health_check": {
                            "path": "/health",
                        },
                    },
                }
            ]
        }
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []

        result = AbstractAgent._apply_model_definition(
            Mock(), raw_definition, model_folder, environ, service_ports
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 60
        assert health_check["max_retries"] == 10
        assert health_check["max_wait_time"] == 15


class TestLoadModelDefinition:
    """Tests for AbstractAgent.load_model_definition()."""

    async def test_uses_model_definition_from_internal_data(self) -> None:
        """When internal_data contains model_definition, it should be used."""
        model_definition = _make_model_definition(initial_delay=300, max_retries=30)
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test-image:latest"},
            "internal_data": {
                "model_definition": model_definition,
                "runtime_variant": "vllm",
            },
        }

        mock_agent = Mock(spec=AbstractAgent)
        mock_agent._apply_model_definition = AbstractAgent._apply_model_definition.__get__(
            mock_agent
        )
        mock_agent.load_model_definition = AbstractAgent.load_model_definition.__get__(mock_agent)

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"),
            [model_folder],
            environ,
            service_ports,
            kernel_config,
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 300
        assert health_check["max_retries"] == 30

    async def test_raises_error_when_model_definition_absent(self) -> None:
        """When internal_data has no model_definition, raise ModelDefinitionNotFoundError."""
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test-image:latest"},
            "internal_data": {
                "runtime_variant": "vllm",
            },
        }

        mock_agent = Mock(spec=AbstractAgent)
        mock_agent._apply_model_definition = AbstractAgent._apply_model_definition.__get__(
            mock_agent
        )
        mock_agent.load_model_definition = AbstractAgent.load_model_definition.__get__(mock_agent)

        with pytest.raises(ModelDefinitionNotFoundError):
            await mock_agent.load_model_definition(
                RuntimeVariant("vllm"),
                [model_folder],
                environ,
                service_ports,
                kernel_config,
            )

    async def test_raises_error_when_internal_data_missing(self) -> None:
        """When internal_data is None, raise ModelDefinitionNotFoundError."""
        model_folder = _make_vfolder_mount()
        environ: dict[str, Any] = {}
        service_ports: list[ServicePort] = []
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test-image:latest"},
            "internal_data": None,
        }

        mock_agent = Mock(spec=AbstractAgent)
        mock_agent.load_model_definition = AbstractAgent.load_model_definition.__get__(mock_agent)

        with pytest.raises(ModelDefinitionNotFoundError):
            await mock_agent.load_model_definition(
                RuntimeVariant("custom"),
                [model_folder],
                environ,
                service_ports,
                kernel_config,
            )
