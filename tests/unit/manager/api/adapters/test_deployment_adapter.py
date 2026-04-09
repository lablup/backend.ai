"""Unit tests for DeploymentAdapter DTO conversions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.common.config import ModelConfig, ModelDefinition, ModelServiceConfig
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.api.adapters.deployment import DeploymentAdapter
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ResourceConfigData,
)


class TestRevisionDataToDTO:
    """Tests for DeploymentAdapter._revision_data_to_dto conversion."""

    def test_model_definition_is_mapped_to_revision_dto(self) -> None:
        revision = ModelRevisionData(
            id=uuid4(),
            name="revision-1",
            cluster_config=ClusterConfigData(
                mode=ClusterMode.SINGLE_NODE,
                size=1,
            ),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "2"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant=RuntimeVariant("custom"),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=uuid4(),
                mount_destination="/models",
                definition_path="model-definition.yaml",
            ),
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="demo-model",
                        model_path="/models/demo",
                        service=ModelServiceConfig(
                            start_command="python serve.py",
                            port=8000,
                        ),
                    ),
                ],
            ),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            image_id=uuid4(),
            extra_vfolder_mounts=[],
        )

        dto = DeploymentAdapter._revision_data_to_dto(revision)

        assert dto.model_definition is not None
        assert dto.model_definition.models[0].name == "demo-model"
        assert dto.model_definition.models[0].service is not None
        assert dto.model_definition.models[0].service.port == 8000
