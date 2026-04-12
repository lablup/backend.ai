"""Tests for model definition loading from Manager-provided internal_data."""

from __future__ import annotations

from dataclasses import dataclass
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


@pytest.fixture
def model_folder() -> VFolderMount:
    mock = MagicMock(spec=VFolderMount)
    mock.name = "test-model"
    mock.vfid = MagicMock()
    mock.vfid.folder_id = UUID("00000000-0000-0000-0000-000000000001")
    mock.kernel_path = MagicMock()
    mock.kernel_path.as_posix.return_value = "/models"
    mock.host_path = MagicMock()
    return mock


@pytest.fixture
def environ() -> dict[str, Any]:
    return {}


@pytest.fixture
def service_ports() -> list[ServicePort]:
    return []


def _make_model_definition(
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


def _make_model_definition_health_check_path_only() -> dict[str, Any]:
    return {
        "models": [
            {
                "name": "vllm-model",
                "model_path": "/models",
                "service": {
                    "start_command": "vllm serve",
                    "port": 8000,
                    "health_check": {"path": "/health"},
                },
            }
        ]
    }


@dataclass
class HealthCheckParams:
    initial_delay: float
    max_retries: int
    max_wait_time: float


@dataclass
class MissingDefinitionCase:
    internal_data: dict[str, Any] | None


class TestApplyModelDefinition:
    """Tests for AbstractAgent._apply_model_definition()."""

    @pytest.mark.parametrize(
        "params",
        [
            HealthCheckParams(initial_delay=300, max_retries=30, max_wait_time=20),
            HealthCheckParams(initial_delay=600, max_retries=60, max_wait_time=30),
            HealthCheckParams(initial_delay=0, max_retries=1, max_wait_time=5),
        ],
        ids=["large-model", "very-large-model", "minimal"],
    )
    def test_applies_custom_health_check_values(
        self,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
        params: HealthCheckParams,
    ) -> None:
        raw_definition = _make_model_definition(
            initial_delay=params.initial_delay,
            max_retries=params.max_retries,
            max_wait_time=params.max_wait_time,
        )

        result = AbstractAgent._apply_model_definition(
            Mock(), raw_definition, model_folder, environ, service_ports
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == params.initial_delay
        assert health_check["max_retries"] == params.max_retries
        assert health_check["max_wait_time"] == params.max_wait_time

    def test_sets_environ_variables(
        self,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        AbstractAgent._apply_model_definition(
            Mock(), _make_model_definition(), model_folder, environ, service_ports
        )

        assert environ["BACKEND_MODEL_NAME"] == "vllm-model"
        assert environ["BACKEND_MODEL_PATH"] == "/models"

    def test_appends_service_port(
        self,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        AbstractAgent._apply_model_definition(
            Mock(), _make_model_definition(), model_folder, environ, service_ports
        )

        assert len(service_ports) == 1
        assert service_ports[0]["container_ports"] == (8000,)
        assert service_ports[0]["is_inference"] is True

    def test_applies_trafaret_defaults_when_health_check_has_path_only(
        self,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        result = AbstractAgent._apply_model_definition(
            Mock(),
            _make_model_definition_health_check_path_only(),
            model_folder,
            environ,
            service_ports,
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 60
        assert health_check["max_retries"] == 10
        assert health_check["max_wait_time"] == 15


@pytest.fixture
def mock_agent() -> Mock:
    agent = Mock(spec=AbstractAgent)
    agent._apply_model_definition = AbstractAgent._apply_model_definition.__get__(agent)
    agent.load_model_definition = AbstractAgent.load_model_definition.__get__(agent)
    return agent


class TestLoadModelDefinition:
    """Tests for AbstractAgent.load_model_definition()."""

    async def test_uses_model_definition_from_internal_data(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        model_definition = _make_model_definition(initial_delay=300, max_retries=30)
        kernel_config: dict[str, Any] = {
            "internal_data": {"model_definition": model_definition},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 300
        assert health_check["max_retries"] == 30

    @pytest.mark.parametrize(
        "case",
        [
            MissingDefinitionCase(internal_data={"runtime_variant": "vllm"}),
            MissingDefinitionCase(internal_data=None),
            MissingDefinitionCase(internal_data={}),
        ],
        ids=["no-model-definition", "internal-data-none", "internal-data-empty"],
    )
    async def test_raises_error_when_model_definition_absent(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
        case: MissingDefinitionCase,
    ) -> None:
        kernel_config: dict[str, Any] = {"internal_data": case.internal_data}

        with pytest.raises(ModelDefinitionNotFoundError):
            await mock_agent.load_model_definition(
                RuntimeVariant("vllm"),
                [model_folder],
                environ,
                service_ports,
                kernel_config,
            )
