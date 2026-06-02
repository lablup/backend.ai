"""Unit tests for DeploymentAdapter DTO conversions."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.config import ModelConfig, ModelDefinition, ModelServiceConfig
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.manager.api.adapters.deployment.adapter import (
    DeploymentAdapter,
    _tristate_from_input,
)
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.types import TriState


class TestRevisionDataToDTO:
    """Tests for DeploymentAdapter._revision_data_to_dto conversion."""

    def test_model_definition_is_mapped_to_revision_dto(self) -> None:
        revision = ModelRevisionData(
            id=DeploymentRevisionID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            revision_number=1,
            cluster_config=ClusterConfigData(
                mode=ClusterMode.SINGLE_NODE,
                size=1,
            ),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "2"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(uuid4()),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=VFolderUUID(uuid4()),
                mount_destination="/models",
                definition_path="model-definition.yaml",
                extra_mounts=[],
            ),
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="demo-model",
                        model_path="/models/demo",
                        service=ModelServiceConfig(
                            start_command=["python", "serve.py"],
                            port=8000,
                        ),
                    ),
                ],
            ),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            image_id=ImageID(uuid4()),
            execution=ExecutionData(
                startup_command=None,
                bootstrap_script=None,
                callback_url=None,
            ),
            preset=PresetAttributionData(preset_id=None, values=[]),
        )

        dto = DeploymentAdapter._revision_data_to_dto(revision)

        assert dto.model_definition is not None
        assert dto.model_definition.models[0].name == "demo-model"
        service = dto.model_definition.models[0].service
        assert service is not None
        assert service.port == 8000
        assert service.start_command == ["python", "serve.py"]


class TestTriStateFromInput:
    """Tests for _tristate_from_input(): Sentinel/None/value → NOP/NULLIFY/UPDATE."""

    def test_sentinel_yields_nop(self) -> None:
        result: TriState[Decimal] = _tristate_from_input(SENTINEL)
        assert result.is_nop()

    def test_none_yields_nullify(self) -> None:
        result: TriState[Decimal] = _tristate_from_input(None)
        assert result.is_nullify()

    def test_decimal_value_yields_update(self) -> None:
        result = _tristate_from_input(Decimal("0.5"))
        assert result.is_update()
        assert result.value() == Decimal("0.5")

    def test_uuid_value_yields_update(self) -> None:
        preset_id = uuid4()
        result = _tristate_from_input(preset_id)
        assert result.is_update()
        assert result.value() == preset_id

    def test_int_value_yields_update(self) -> None:
        result = _tristate_from_input(3)
        assert result.is_update()
        assert result.value() == 3
