"""Regression tests for DeploymentRevisionPreset GraphQL type conversions.

These tests pin down the Strawberry ``from_pydantic`` mapping for nested
output types, guarding against silent field-name / type mismatches between
the Pydantic DTO and the GraphQL type (BA-5931).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.config import ModelConfig, ModelDefinition
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
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
    PresetExecutionSpecGQL,
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
            startup_command=None,
            bootstrap_script=None,
            environ=[],
        ),
        deployment_defaults=PresetDeploymentDefaults(),
        model_definition=model_definition,
        preset_values=[],
        created_at=now,
        updated_at=None,
    )


class TestPresetExecutionSpecGQL:
    def test_image_id_is_mapped_from_dto(self) -> None:
        """BA-5931: GQL must expose ``image_id`` matching the DTO field name."""
        image_id = ImageID(uuid.uuid4())
        dto = PresetExecutionSpec(
            image_id=image_id,
            startup_command="serve",
            bootstrap_script="setup.sh",
            environ=[],
        )

        gql = PresetExecutionSpecGQL.from_pydantic(dto)

        assert gql.image_id == uuid.UUID(str(image_id))
        assert gql.startup_command == "serve"
        assert gql.bootstrap_script == "setup.sh"

    def test_image_id_none_when_dto_image_id_is_none(self) -> None:
        dto = PresetExecutionSpec(image_id=None)

        gql = PresetExecutionSpecGQL.from_pydantic(dto)

        assert gql.image_id is None


class TestDeploymentRevisionPresetGQL:
    def test_execution_image_id_round_trips_through_node(self) -> None:
        """BA-5931: nested ``execution.image_id`` must survive node-level conversion."""
        image_id = ImageID(uuid.uuid4())
        node = _make_preset_node(image_id=image_id)

        gql = DeploymentRevisionPresetGQL.from_pydantic(node)

        assert gql.execution.image_id == uuid.UUID(str(image_id))

    def test_model_definition_is_mapped_from_dto(self) -> None:
        """BA-5931: nested ``model_definition`` must convert via ModelDefinitionInfoDTO."""
        model_def = ModelDefinitionInfoDTO(
            models=[
                ModelConfigInfoDTO(
                    name="llama",
                    model_path="/models/llama",
                    service=None,
                    metadata=None,
                ),
            ],
        )
        node = _make_preset_node(model_definition=model_def)

        gql = DeploymentRevisionPresetGQL.from_pydantic(node)

        assert gql.model_definition is not None
        assert len(gql.model_definition.models) == 1
        assert gql.model_definition.models[0].name == "llama"
        assert gql.model_definition.models[0].model_path == "/models/llama"

    def test_model_definition_none_when_absent(self) -> None:
        node = _make_preset_node(model_definition=None)

        gql = DeploymentRevisionPresetGQL.from_pydantic(node)

        assert gql.model_definition is None

    def test_adapter_converts_config_model_definition_to_dto(self) -> None:
        """Adapter helper must bridge ``ModelDefinition`` (config) to ``ModelDefinitionInfoDTO``."""
        config_model_def = ModelDefinition(
            models=[ModelConfig(name="llama", model_path="/models/llama")],
        )

        info_dto = _model_definition_to_dto(config_model_def)

        assert len(info_dto.models) == 1
        assert info_dto.models[0].name == "llama"
        assert info_dto.models[0].model_path == "/models/llama"
