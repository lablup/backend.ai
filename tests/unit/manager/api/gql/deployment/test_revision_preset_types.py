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


def test_deployment_revision_preset_gql_from_pydantic() -> None:
    image_id = ImageID(uuid.uuid4())
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

    empty = DeploymentRevisionPresetGQL.from_pydantic(_make_preset_node())

    assert empty.execution.image_id is None
    assert empty.model_definition is None


def test_model_definition_to_dto_converts_config_to_info_dto() -> None:
    config_model_def = ModelDefinition(
        models=[ModelConfig(name="llama", model_path="/models/llama")],
    )

    info_dto = _model_definition_to_dto(config_model_def)

    assert info_dto is not None
    assert len(info_dto.models) == 1
    assert info_dto.models[0].name == "llama"
    assert info_dto.models[0].model_path == "/models/llama"
    assert _model_definition_to_dto(None) is None
