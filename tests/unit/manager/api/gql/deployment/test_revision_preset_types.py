from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.config import DEFAULT_SHELL, ModelConfig, ModelDefinition
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
    ModelServiceConfigInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    PresetModelConfigInput,
    PresetModelDefinitionInput,
    PresetModelHealthCheckInput,
    PresetModelServiceConfigInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
    PresetClusterSpec,
    PresetDeploymentDefaults,
    PresetExecutionSpec,
    PresetResourceAllocation,
)
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    _model_definition_to_dto,
)
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetGQL,
    PresetModelConfigInputGQL,
    PresetModelDefinitionInputGQL,
    PresetModelHealthCheckInputGQL,
    PresetModelServiceConfigInputGQL,
)


def _make_preset_node(
    *,
    image_id: ImageID | None = None,
    model_definition: ModelDefinitionInfoDTO | None = None,
) -> DeploymentRevisionPresetNode:
    now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    return DeploymentRevisionPresetNode(
        id=uuid.uuid4(),
        runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
        name="preset",
        description=None,
        rank=100,
        cluster=PresetClusterSpec(cluster_mode="single-node", cluster_size=1),
        resource=PresetResourceAllocation(resource_opts=[]),
        execution=PresetExecutionSpec(
            image_id=image_id,
            startup_command="serve",
            bootstrap_script="setup.sh",
            environ=[],
        ),
        deployment_defaults=PresetDeploymentDefaults(),
        model_definition=model_definition,
        preset_values=[],
        created_at=now,
        updated_at=None,
    )


class TestDeploymentRevisionPresetGQL:
    """Tests for ``DeploymentRevisionPresetGQL.from_pydantic`` output conversion."""

    def test_from_pydantic_populates_execution_and_model_definition(self) -> None:
        image_id = ImageID(uuid.uuid4())
        model_def = ModelDefinitionInfoDTO(
            models=[
                ModelConfigInfoDTO(
                    name="llama",
                    model_path="/models/llama",
                    service=ModelServiceConfigInfoDTO(port=8080),
                    metadata=None,
                ),
            ],
        )

        populated = DeploymentRevisionPresetGQL.from_pydantic(
            _make_preset_node(image_id=image_id, model_definition=model_def),
        )

        assert populated.execution.image_id == uuid.UUID(str(image_id))
        assert populated.execution.startup_command == "serve"
        assert populated.execution.bootstrap_script == "setup.sh"
        assert populated.model_definition is not None
        assert len(populated.model_definition.models) == 1
        assert populated.model_definition.models[0].name == "llama"
        assert populated.model_definition.models[0].model_path == "/models/llama"

    def test_from_pydantic_handles_empty_execution_and_model_definition(self) -> None:
        empty = DeploymentRevisionPresetGQL.from_pydantic(_make_preset_node())

        assert empty.execution.image_id is None
        assert empty.model_definition is None


class TestModelDefinitionToDTO:
    """Tests for the adapter helper ``_model_definition_to_dto``."""

    def test_converts_config_to_info_dto(self) -> None:
        config_model_def = ModelDefinition(
            models=[ModelConfig(name="llama", model_path="/models/llama")],
        )

        info_dto = _model_definition_to_dto(config_model_def)

        assert info_dto is not None
        assert len(info_dto.models) == 1
        assert info_dto.models[0].name == "llama"
        assert info_dto.models[0].model_path == "/models/llama"

    def test_returns_none_for_none(self) -> None:
        assert _model_definition_to_dto(None) is None


class TestPresetModelDefinitionInputGQL:
    """Tests for the strict CREATE-only model_definition GQL input → request DTO conversion."""

    def test_to_pydantic_produces_strict_request_dto(self) -> None:
        gql_input = PresetModelDefinitionInputGQL(
            models=[
                PresetModelConfigInputGQL(
                    name="llama",
                    model_path="/models/llama",
                    service=PresetModelServiceConfigInputGQL(
                        port=8080,
                        start_command=["python", "server.py"],
                    ),
                ),
            ],
        )

        dto = gql_input.to_pydantic()

        assert isinstance(dto, PresetModelDefinitionInput)
        assert len(dto.models) == 1
        config = dto.models[0]
        assert isinstance(config, PresetModelConfigInput)
        assert config.name == "llama"
        assert config.model_path == "/models/llama"
        assert isinstance(config.service, PresetModelServiceConfigInput)
        assert config.service.port == 8080
        assert config.service.start_command == ["python", "server.py"]
        # request-DTO defaults mirror the strict config defaults
        assert config.service.shell == DEFAULT_SHELL
        assert config.service.pre_start_actions == []
        assert config.service.health_check is None
        assert config.metadata is None

    def test_service_config_carries_health_check_defaults(self) -> None:
        with_hc = PresetModelServiceConfigInputGQL(
            port=9000,
            start_command=["python", "server.py"],
            health_check=PresetModelHealthCheckInputGQL(enable=True),
        ).to_pydantic()

        assert isinstance(with_hc.health_check, PresetModelHealthCheckInput)
        assert with_hc.health_check.enable is True
        # omitted health-check fields fall back to the request-DTO defaults
        assert with_hc.health_check.interval == 10.0
        assert with_hc.health_check.path == "/health"
        assert with_hc.health_check.initial_delay == 1800.0


class TestPresetModelDefinitionInput:
    """Tests for the strict request DTO's field-level enforcement."""

    def test_rejects_empty_models(self) -> None:
        with pytest.raises(ValidationError):
            PresetModelDefinitionInput(models=[])

    def test_rejects_multiple_models(self) -> None:
        # Exactly one model is supported (max_length=1).
        config = PresetModelConfigInput(
            name="llama",
            model_path="/models/llama",
            service=PresetModelServiceConfigInput(port=8080, start_command=["python", "s.py"]),
        )
        with pytest.raises(ValidationError):
            PresetModelDefinitionInput(models=[config, config])

    def test_rejects_model_without_service(self) -> None:
        # ``service`` is a required field; omitting it must be rejected.
        payload: dict[str, Any] = {"name": "llama", "model_path": "/models/llama"}
        with pytest.raises(ValidationError):
            PresetModelConfigInput(**payload)

    def test_rejects_service_without_start_command(self) -> None:
        # ``start_command`` is a required field; omitting it must be rejected.
        payload: dict[str, Any] = {"port": 8080}
        with pytest.raises(ValidationError):
            PresetModelServiceConfigInput(**payload)

    def test_accepts_fully_populated(self) -> None:
        dto = PresetModelDefinitionInput(
            models=[
                PresetModelConfigInput(
                    name="llama",
                    model_path="/models/llama",
                    service=PresetModelServiceConfigInput(
                        port=8080,
                        start_command=["python", "server.py"],
                    ),
                ),
            ],
        )

        assert len(dto.models) == 1
        assert dto.models[0].service.port == 8080


class TestCreateDeploymentRevisionPresetInput:
    """Tests for the CREATE input's optional model_definition handling."""

    def test_accepts_populated_model_definition(self) -> None:
        dto = CreateDeploymentRevisionPresetInput(
            runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            name="populated-models",
            image_id=ImageID(uuid.uuid4()),
            model_definition=PresetModelDefinitionInput(
                models=[
                    PresetModelConfigInput(
                        name="llama",
                        model_path="/models/llama",
                        service=PresetModelServiceConfigInput(
                            port=8080,
                            start_command=["python", "server.py"],
                        ),
                    ),
                ],
            ),
            cluster_mode="single-node",
            cluster_size=1,
            replica_count=1,
            deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
        )

        assert dto.model_definition is not None
        assert len(dto.model_definition.models) == 1

    def test_allows_null_model_definition(self) -> None:
        dto = CreateDeploymentRevisionPresetInput(
            runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            name="no-models",
            image_id=ImageID(uuid.uuid4()),
            model_definition=None,
            cluster_mode="single-node",
            cluster_size=1,
            replica_count=1,
            deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
        )

        assert dto.model_definition is None
