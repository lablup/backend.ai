"""Tests for model definition loading with VFolder override for non-custom variants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock
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
def vfolder_path(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def model_folder(vfolder_path: Path) -> VFolderMount:
    mock = MagicMock(spec=VFolderMount)
    mock.name = "test-model"
    mock.vfid = MagicMock()
    mock.vfid.folder_id = UUID("00000000-0000-0000-0000-000000000001")
    mock.kernel_path = MagicMock()
    mock.kernel_path.as_posix.return_value = "/models"
    mock.host_path = vfolder_path
    return mock


@pytest.fixture
def environ() -> dict[str, Any]:
    return {}


@pytest.fixture
def service_ports() -> list[ServicePort]:
    return []


@pytest.fixture
def mock_agent() -> Mock:
    agent = Mock(spec=AbstractAgent)
    agent.extract_image_command = AsyncMock(return_value="vllm serve")
    agent.load_model_definition = AbstractAgent.load_model_definition.__get__(agent)
    agent._read_model_definition_from_vfolder = (
        AbstractAgent._read_model_definition_from_vfolder.__get__(agent)
    )
    agent._try_read_model_definition_from_vfolder = (
        AbstractAgent._try_read_model_definition_from_vfolder.__get__(agent)
    )
    return agent


def _write_model_definition_yaml(
    vfolder_path: Path,
    initial_delay: float = 300,
    max_retries: int = 30,
    max_wait_time: float = 20,
) -> None:
    (vfolder_path / "model-definition.yaml").write_text(f"""\
models:
  - name: "override-model"
    model_path: "/models"
    service:
      start_command: "serve"
      port: 8000
      health_check:
        path: /health
        initial_delay: {initial_delay}
        max_retries: {max_retries}
        max_wait_time: {max_wait_time}
""")


@dataclass
class HealthCheckOverrideCase:
    initial_delay: float
    max_retries: int
    max_wait_time: float


class TestVFolderOverrideForNonCustomVariants:
    """Tests for VFolder model-definition.yaml override on non-custom variants."""

    @pytest.mark.parametrize(
        "case",
        [
            HealthCheckOverrideCase(initial_delay=300, max_retries=30, max_wait_time=20),
            HealthCheckOverrideCase(initial_delay=600, max_retries=60, max_wait_time=30),
        ],
        ids=["large-model", "very-large-model"],
    )
    async def test_vfolder_override_applied_for_vllm(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
        case: HealthCheckOverrideCase,
    ) -> None:
        _write_model_definition_yaml(
            vfolder_path,
            initial_delay=case.initial_delay,
            max_retries=case.max_retries,
            max_wait_time=case.max_wait_time,
        )
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test:latest"},
            "internal_data": {"runtime_variant": "vllm"},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == case.initial_delay
        assert health_check["max_retries"] == case.max_retries
        assert health_check["max_wait_time"] == case.max_wait_time

    async def test_no_vfolder_yaml_uses_hardcoded_defaults(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        # No model-definition.yaml written to tmp_path
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test:latest"},
            "internal_data": {"runtime_variant": "vllm"},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        health_check = result["models"][0]["service"]["health_check"]
        # trafaret defaults
        assert health_check["initial_delay"] == 60
        assert health_check["max_retries"] == 10
        assert health_check["max_wait_time"] == 15

    async def test_invalid_yaml_falls_back_to_defaults(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        (vfolder_path / "model-definition.yaml").write_text("not: [valid: yaml: {")
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test:latest"},
            "internal_data": {"runtime_variant": "vllm"},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        # Invalid yaml should be skipped, hardcoded defaults used
        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 60

    async def test_non_mapping_yaml_falls_back_to_defaults(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        (vfolder_path / "model-definition.yaml").write_text("- just\n- a\n- list\n")
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test:latest"},
            "internal_data": {"runtime_variant": "vllm"},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 60

    async def test_merge_failure_falls_back_to_defaults(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
        environ: dict[str, Any],
        service_ports: list[ServicePort],
    ) -> None:
        # Valid YAML, valid mapping, but invalid ModelDefinition structure
        (vfolder_path / "model-definition.yaml").write_text("something: unexpected\n")
        kernel_config: dict[str, Any] = {
            "image": {"canonical": "test:latest"},
            "internal_data": {"runtime_variant": "vllm"},
        }

        result = await mock_agent.load_model_definition(
            RuntimeVariant("vllm"), [model_folder], environ, service_ports, kernel_config
        )

        # merge should fail, fall back to variant defaults
        health_check = result["models"][0]["service"]["health_check"]
        assert health_check["initial_delay"] == 60


class TestVFolderReadHelpers:
    """Tests for _read_model_definition_from_vfolder and _try variants."""

    async def test_read_returns_parsed_yaml(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
    ) -> None:
        _write_model_definition_yaml(vfolder_path)
        kernel_config: dict[str, Any] = {"internal_data": {}}

        result = await mock_agent._read_model_definition_from_vfolder(model_folder, kernel_config)

        assert isinstance(result, dict)
        assert result["models"][0]["name"] == "override-model"

    async def test_read_raises_on_missing_file(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
    ) -> None:
        kernel_config: dict[str, Any] = {"internal_data": {}}

        with pytest.raises(ModelDefinitionNotFoundError):
            await mock_agent._read_model_definition_from_vfolder(model_folder, kernel_config)

    async def test_try_read_returns_none_on_missing_file(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
    ) -> None:
        kernel_config: dict[str, Any] = {"internal_data": {}}

        result = await mock_agent._try_read_model_definition_from_vfolder(
            model_folder, kernel_config
        )

        assert result is None

    async def test_try_read_returns_none_on_invalid_yaml(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
    ) -> None:
        (vfolder_path / "model-definition.yaml").write_text("{invalid yaml")
        kernel_config: dict[str, Any] = {"internal_data": {}}

        result = await mock_agent._try_read_model_definition_from_vfolder(
            model_folder, kernel_config
        )

        assert result is None

    async def test_uses_model_definition_path_from_internal_data(
        self,
        mock_agent: Mock,
        model_folder: VFolderMount,
        vfolder_path: Path,
    ) -> None:
        (vfolder_path / "custom-name.yaml").write_text(
            "models:\n  - name: custom\n    model_path: /m\n"
        )
        kernel_config: dict[str, Any] = {
            "internal_data": {"model_definition_path": "custom-name.yaml"},
        }

        result = await mock_agent._read_model_definition_from_vfolder(model_folder, kernel_config)

        assert result["models"][0]["name"] == "custom"
