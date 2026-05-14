"""Tests for ai.backend.common.dto.manager.v2.deployment.request module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateDeploymentInput,
    AddRevisionInput,
    BlueGreenConfigInput,
    ClusterConfigInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
    CreateRevisionInput,
    DeleteDeploymentInput,
    DeploymentStrategyInput,
    ExtraVFolderMountInput,
    ImageInput,
    ModelDefinitionInput,
    ModelDeploymentMetadataInput,
    ModelDeploymentNetworkAccessInput,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    ResourceConfigInput,
    ResourceSlotEntryInput,
    ResourceSlotInput,
    RollingUpdateConfigInput,
    ScaleDeploymentInput,
    UpdateDeploymentInput,
)
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode


def _make_create_revision_input_dto(**kwargs: object) -> CreateRevisionInput:
    defaults: dict[str, Any] = {
        "cluster_config": ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
        "resource_config": ResourceConfigInput(
            resource_slots=ResourceSlotInput(
                entries=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity="2"),
                    ResourceSlotEntryInput(resource_type="mem", quantity="4g"),
                ]
            ),
        ),
        "image": ImageInput(id=ImageID(uuid.uuid4())),
        "model_runtime_config": ModelRuntimeConfigInput(
            runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
        ),
        "model_mount_config": ModelMountConfigInput(
            vfolder_id=VFolderUUID(uuid.uuid4()),
            mount_destination="/models",
            definition_path="/models/model.yaml",
        ),
        "model_definition": ModelDefinitionInput(),
    }
    defaults.update(kwargs)
    return CreateRevisionInput(**defaults)


class TestExtraVFolderMountInput:
    """Tests for ExtraVFolderMountInput model."""

    def test_valid_creation(self) -> None:
        vfolder_id = VFolderUUID(uuid.uuid4())
        mount = ExtraVFolderMountInput(vfolder_id=vfolder_id, mount_destination="/data")
        assert mount.vfolder_id == vfolder_id
        assert mount.mount_destination == "/data"

    def test_mount_destination_defaults_to_none(self) -> None:
        mount = ExtraVFolderMountInput(vfolder_id=VFolderUUID(uuid.uuid4()))
        assert mount.mount_destination is None

    def test_missing_vfolder_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ExtraVFolderMountInput.model_validate({})


@dataclass(frozen=True)
class RollingUpdateValidScenario:
    """A valid RollingUpdateConfigInput test scenario."""

    surge: IntOrPercent
    unavailable: IntOrPercent
    expected_surge_value: int | float
    expected_unavailable_value: int | float


class TestRollingUpdateConfigInput:
    """Tests for RollingUpdateConfigInput model."""

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                RollingUpdateValidScenario(
                    surge=IntOrPercent(count=2),
                    unavailable=IntOrPercent(count=1),
                    expected_surge_value=2,
                    expected_unavailable_value=1,
                ),
                id="count",
            ),
            pytest.param(
                RollingUpdateValidScenario(
                    surge=IntOrPercent(percent=0.25),
                    unavailable=IntOrPercent(percent=0.5),
                    expected_surge_value=0.25,
                    expected_unavailable_value=0.5,
                ),
                id="percent",
            ),
        ],
    )
    def test_valid_surge_values(self, scenario: RollingUpdateValidScenario) -> None:
        config = RollingUpdateConfigInput(
            max_surge=scenario.surge, max_unavailable=scenario.unavailable
        )
        if scenario.surge.is_count:
            assert config.max_surge.count == scenario.expected_surge_value
            assert config.max_unavailable.count == scenario.expected_unavailable_value
        else:
            assert config.max_surge.percent == scenario.expected_surge_value
            assert config.max_unavailable.percent == scenario.expected_unavailable_value

    def test_defaults(self) -> None:
        config = RollingUpdateConfigInput()
        assert config.max_surge.is_percent
        assert config.max_surge.percent == 0.5
        assert config.max_unavailable.is_percent
        assert config.max_unavailable.percent == 0.0

    @pytest.mark.parametrize(
        "raw_input",
        [
            pytest.param(
                {"max_surge": {"count": -1}},
                id="surge_negative_count",
            ),
            pytest.param(
                {"max_surge": {"percent": 1.5}},
                id="surge_percent_over_1",
            ),
            pytest.param(
                {"max_surge": {"percent": -0.1}},
                id="surge_negative_percent",
            ),
            pytest.param(
                {"max_surge": {"count": 2, "percent": 0.5}},
                id="surge_both_fields_set",
            ),
            pytest.param(
                {"max_surge": {}},
                id="surge_neither_field_set",
            ),
            pytest.param(
                {"max_unavailable": {"count": -1}},
                id="unavailable_negative_count",
            ),
            pytest.param(
                {"max_unavailable": {"percent": 1.5}},
                id="unavailable_percent_over_1",
            ),
            pytest.param(
                {"max_unavailable": {"percent": -0.1}},
                id="unavailable_negative_percent",
            ),
            pytest.param(
                {"max_unavailable": {"count": 0, "percent": 0.0}},
                id="unavailable_both_fields_set",
            ),
            pytest.param(
                {"max_unavailable": {}},
                id="unavailable_neither_field_set",
            ),
        ],
    )
    def test_invalid_input_raises_error(self, raw_input: dict[str, object]) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            RollingUpdateConfigInput.model_validate(raw_input)


class TestBlueGreenConfigInput:
    """Tests for BlueGreenConfigInput model."""

    def test_valid_creation(self) -> None:
        config = BlueGreenConfigInput(auto_promote=True, promote_delay_seconds=60)
        assert config.auto_promote is True
        assert config.promote_delay_seconds == 60

    def test_defaults(self) -> None:
        config = BlueGreenConfigInput()
        assert config.auto_promote is False
        assert config.promote_delay_seconds == 0

    def test_negative_delay_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            BlueGreenConfigInput(promote_delay_seconds=-1)


class TestCreateDeploymentInput:
    """Tests for CreateDeploymentInput model creation and validation."""

    def _make_metadata(self, **kwargs: object) -> ModelDeploymentMetadataInput:
        defaults: dict[str, Any] = {
            "project_id": uuid.uuid4(),
            "domain_name": "default",
            "resource_group_name": "default",
        }
        defaults.update(kwargs)
        return ModelDeploymentMetadataInput(**defaults)

    def _make_input(self, **kwargs: object) -> CreateDeploymentInput:
        defaults: dict[str, Any] = {
            "metadata": self._make_metadata(),
            "network_access": ModelDeploymentNetworkAccessInput(),
            "default_deployment_strategy": DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            "replica_count": 2,
            "initial_revision": _make_create_revision_input_dto(),
        }
        defaults.update(kwargs)
        return CreateDeploymentInput(**defaults)

    def test_valid_creation_with_required_fields(self) -> None:
        project_id = uuid.uuid4()
        inp = self._make_input(
            metadata=self._make_metadata(project_id=project_id),
        )
        assert inp.metadata.project_id == project_id
        assert inp.metadata.domain_name == "default"
        assert inp.default_deployment_strategy.type == DeploymentStrategy.ROLLING
        assert inp.replica_count == 2

    def test_default_open_to_public_is_false(self) -> None:
        inp = self._make_input()
        assert inp.network_access.open_to_public is False

    def test_optional_name_defaults_to_none(self) -> None:
        inp = self._make_input()
        assert inp.metadata.name is None

    def test_optional_tags_defaults_to_none(self) -> None:
        inp = self._make_input()
        assert inp.metadata.tags is None

    def test_name_whitespace_is_stripped(self) -> None:
        inp = self._make_input(
            metadata=self._make_metadata(name="  my-deployment  "),
        )
        assert inp.metadata.name == "my-deployment"

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            self._make_input(
                metadata=self._make_metadata(name="   "),
            )

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            self._make_input(
                metadata=self._make_metadata(name=""),
            )

    def test_replica_count_zero_is_valid(self) -> None:
        inp = self._make_input(replica_count=0)
        assert inp.replica_count == 0

    def test_negative_replica_count_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            self._make_input(replica_count=-1)

    def test_blue_green_strategy(self) -> None:
        inp = self._make_input(
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.BLUE_GREEN,
            ),
        )
        assert inp.default_deployment_strategy.type == DeploymentStrategy.BLUE_GREEN

    def test_with_rolling_update_config(self) -> None:
        rolling = RollingUpdateConfigInput(
            max_surge=IntOrPercent(count=2),
            max_unavailable=IntOrPercent(count=1),
        )
        inp = self._make_input(
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
                rolling_update=rolling,
            ),
        )
        assert inp.default_deployment_strategy.rolling_update is not None
        assert inp.default_deployment_strategy.rolling_update.max_surge.count == 2

    def test_with_blue_green_config(self) -> None:
        bg = BlueGreenConfigInput(auto_promote=True, promote_delay_seconds=30)
        inp = self._make_input(
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.BLUE_GREEN,
                blue_green=bg,
            ),
        )
        assert inp.default_deployment_strategy.blue_green is not None
        assert inp.default_deployment_strategy.blue_green.auto_promote is True

    def test_nested_revision_input(self) -> None:
        image_id = ImageID(uuid.uuid4())
        rev = _make_create_revision_input_dto(image=ImageInput(id=image_id))
        inp = self._make_input(initial_revision=rev)
        assert inp.initial_revision is not None
        assert inp.initial_revision.image.id == image_id

    def test_missing_metadata_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateDeploymentInput.model_validate({
                "network_access": {},
                "default_deployment_strategy": {"type": "ROLLING"},
                "replica_count": 1,
            })


class TestUpdateDeploymentInput:
    """Tests for UpdateDeploymentInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        inp = UpdateDeploymentInput(name=None, replica_count=None, tags=None)
        assert inp.name is None
        assert inp.replica_count is None
        assert inp.tags is None

    def test_default_tags_is_sentinel(self) -> None:
        inp = UpdateDeploymentInput()
        assert inp.tags is SENTINEL
        assert isinstance(inp.tags, Sentinel)

    def test_explicit_sentinel_tags_signals_clear(self) -> None:
        inp = UpdateDeploymentInput(tags=SENTINEL)
        assert inp.tags is SENTINEL
        assert isinstance(inp.tags, Sentinel)

    def test_none_tags_means_no_change(self) -> None:
        inp = UpdateDeploymentInput(tags=None)
        assert inp.tags is None

    def test_string_list_tags_update(self) -> None:
        inp = UpdateDeploymentInput(tags=["tag1", "tag2"])
        assert inp.tags == ["tag1", "tag2"]

    def test_name_whitespace_is_stripped(self) -> None:
        inp = UpdateDeploymentInput(name="  new-name  ")
        assert inp.name == "new-name"

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateDeploymentInput(name="   ")

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateDeploymentInput(name="")

    def test_replica_count_zero_is_valid_for_update(self) -> None:
        inp = UpdateDeploymentInput(replica_count=0)
        assert inp.replica_count == 0

    def test_negative_replicas_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateDeploymentInput(replica_count=-1)

    def test_partial_update_name_only(self) -> None:
        inp = UpdateDeploymentInput(name="updated-name")
        assert inp.name == "updated-name"
        assert inp.replica_count is None


class TestDeleteDeploymentInput:
    """Tests for DeleteDeploymentInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        deployment_id = uuid.uuid4()
        inp = DeleteDeploymentInput(id=deployment_id)
        assert inp.id == deployment_id

    def test_valid_creation_from_uuid_string(self) -> None:
        deployment_id = uuid.uuid4()
        inp = DeleteDeploymentInput.model_validate({"id": str(deployment_id)})
        assert inp.id == deployment_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteDeploymentInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteDeploymentInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        deployment_id = uuid.uuid4()
        inp = DeleteDeploymentInput(id=deployment_id)
        assert isinstance(inp.id, uuid.UUID)


class TestActivateDeploymentInput:
    """Tests for ActivateDeploymentInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        deployment_id = uuid.uuid4()
        inp = ActivateDeploymentInput(id=deployment_id)
        assert inp.id == deployment_id

    def test_valid_creation_from_uuid_string(self) -> None:
        deployment_id = uuid.uuid4()
        inp = ActivateDeploymentInput.model_validate({"id": str(deployment_id)})
        assert inp.id == deployment_id

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ActivateDeploymentInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        deployment_id = uuid.uuid4()
        inp = ActivateDeploymentInput(id=deployment_id)
        assert isinstance(inp.id, uuid.UUID)


class TestScaleDeploymentInput:
    """Tests for ScaleDeploymentInput model creation and validation."""

    def test_valid_creation(self) -> None:
        deployment_id = uuid.uuid4()
        inp = ScaleDeploymentInput(id=deployment_id, replicas=3)
        assert inp.id == deployment_id
        assert inp.replicas == 3

    def test_zero_replicas_is_valid(self) -> None:
        inp = ScaleDeploymentInput(id=uuid.uuid4(), replicas=0)
        assert inp.replicas == 0

    def test_negative_replicas_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScaleDeploymentInput(id=uuid.uuid4(), replicas=-1)

    def test_missing_replicas_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScaleDeploymentInput.model_validate({"id": str(uuid.uuid4())})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScaleDeploymentInput.model_validate({"replicas": 3})


def _make_model_mount_config_input(**kwargs: object) -> ModelMountConfigInput:
    defaults: dict[str, Any] = {
        "vfolder_id": VFolderUUID(uuid.uuid4()),
        "mount_destination": "/models",
        "definition_path": "/models/model.yaml",
    }
    defaults.update(kwargs)
    return ModelMountConfigInput(**defaults)


class TestCreateRevisionInput:
    """Tests for CreateRevisionInput model creation and validation.

    All five sub-configs (cluster_config, resource_config, image,
    model_runtime_config, model_mount_config) are required.
    """

    def test_valid_creation_with_required_fields(self) -> None:
        rev = _make_create_revision_input_dto()
        assert rev.cluster_config.mode == ClusterMode.SINGLE_NODE
        assert rev.image.id is not None
        assert rev.model_mount_config.vfolder_id is not None

    def test_missing_model_mount_config_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRevisionInput.model_validate({
                "cluster_config": {"mode": "SINGLE_NODE", "size": 1},
                "resource_config": {
                    "resource_slots": {"entries": [{"resource_type": "cpu", "quantity": "1"}]}
                },
                "image": {"id": str(uuid.uuid4())},
                "model_runtime_config": {"runtime_variant_id": str(uuid.uuid4())},
            })

    def test_missing_image_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRevisionInput.model_validate({
                "cluster_config": {"mode": "SINGLE_NODE", "size": 1},
                "resource_config": {
                    "resource_slots": {"entries": [{"resource_type": "cpu", "quantity": "1"}]}
                },
                "model_runtime_config": {"runtime_variant_id": str(uuid.uuid4())},
                "model_mount_config": {
                    "vfolder_id": str(uuid.uuid4()),
                    "mount_destination": "/models",
                },
            })

    def test_auto_activate_defaults_to_false(self) -> None:
        rev = _make_create_revision_input_dto()
        assert rev.auto_activate is False

    def test_round_trip(self) -> None:
        rev = _make_create_revision_input_dto()
        restored = CreateRevisionInput.model_validate_json(rev.model_dump_json())
        assert restored.cluster_config.mode == ClusterMode.SINGLE_NODE
        assert restored.model_mount_config.vfolder_id == rev.model_mount_config.vfolder_id


class TestAddRevisionInput:
    """Tests for AddRevisionInput model creation and validation.

    ``deployment_id`` and ``model_mount_config`` are required; every
    other sub-config is optional (the revision merge chain fills in
    missing fields from preset / runtime variant baseline / existing
    revision).
    """

    def test_valid_creation_with_only_required_fields(self) -> None:
        deployment_id = uuid.uuid4()
        mount_config = _make_model_mount_config_input()
        inp = AddRevisionInput(deployment_id=deployment_id, model_mount_config=mount_config)
        assert inp.deployment_id == deployment_id
        assert inp.model_mount_config.vfolder_id == mount_config.vfolder_id

    def test_optional_sub_configs_default_to_none(self) -> None:
        inp = AddRevisionInput(
            deployment_id=uuid.uuid4(),
            model_mount_config=_make_model_mount_config_input(),
        )
        assert inp.cluster_config is None
        assert inp.resource_config is None
        assert inp.image is None
        assert inp.model_runtime_config is None
        assert inp.model_definition is None
        assert inp.extra_mounts is None
        assert inp.options is None
        assert inp.revision_preset_id is None

    def test_missing_model_mount_config_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            AddRevisionInput.model_validate({"deployment_id": str(uuid.uuid4())})

    def test_missing_deployment_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            AddRevisionInput.model_validate({
                "model_mount_config": {
                    "vfolder_id": str(uuid.uuid4()),
                    "mount_destination": "/models",
                }
            })

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        mount_config = _make_model_mount_config_input()
        inp = AddRevisionInput(deployment_id=deployment_id, model_mount_config=mount_config)
        restored = AddRevisionInput.model_validate_json(inp.model_dump_json())
        assert restored.deployment_id == deployment_id
        assert restored.model_mount_config.vfolder_id == mount_config.vfolder_id


class TestCreateAccessTokenInput:
    """Regression tests for CreateAccessTokenInput (BA-5854).

    Verifies that the DTO uses model_deployment_id (matching the GQL/supergraph
    schema) rather than the old deployment_id field name.
    """

    def test_valid_creation(self) -> None:
        deployment_id = uuid.uuid4()
        expires = datetime(2099, 12, 31, 23, 59, 59, tzinfo=UTC)
        inp = CreateAccessTokenInput(model_deployment_id=deployment_id, expires_at=expires)
        assert inp.model_deployment_id == deployment_id
        assert inp.expires_at == expires

    def test_missing_expires_at_raises_validation_error(self) -> None:
        # BA-5881: expires_at is required — there is no safe default lifetime.
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateAccessTokenInput(model_deployment_id=uuid.uuid4())  # type: ignore[call-arg]

    def test_expires_at_none_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateAccessTokenInput.model_validate({
                "model_deployment_id": str(uuid.uuid4()),
                "expires_at": None,
            })

    def test_model_validate_with_isoformat_expires_at_succeeds(self) -> None:
        deployment_id = uuid.uuid4()
        expires = datetime(2099, 1, 1, tzinfo=UTC)
        inp = CreateAccessTokenInput.model_validate({
            "model_deployment_id": str(deployment_id),
            "expires_at": expires.isoformat(),
        })
        assert inp.model_deployment_id == deployment_id
        assert inp.expires_at == expires

    def test_missing_model_deployment_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateAccessTokenInput.model_validate({
                "expires_at": datetime(2099, 1, 1, tzinfo=UTC).isoformat(),
            })

    def test_uuid_string_is_coerced_to_uuid(self) -> None:
        deployment_id = uuid.uuid4()
        inp = CreateAccessTokenInput.model_validate({
            "model_deployment_id": str(deployment_id),
            "expires_at": datetime(2099, 1, 1, tzinfo=UTC).isoformat(),
        })
        assert isinstance(inp.model_deployment_id, uuid.UUID)
        assert inp.model_deployment_id == deployment_id
