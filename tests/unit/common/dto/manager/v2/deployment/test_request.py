"""Tests for ai.backend.common.dto.manager.v2.deployment.request module."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateDeploymentInput,
    AddRevisionInput,
    BlueGreenConfigInput,
    ClusterConfigInput,
    CreateDeploymentInput,
    CreateRevisionInputDTO,
    DeleteDeploymentInput,
    DeploymentStrategyInput,
    ExtraVFolderMountInput,
    ImageInput,
    ModelDeploymentMetadataInput,
    ModelDeploymentNetworkAccessInput,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    ResourceConfigInput,
    ResourceGroupInput,
    ResourceSlotEntryInput,
    ResourceSlotInput,
    RevisionInput,
    RollingUpdateConfigInput,
    ScaleDeploymentInput,
    UpdateDeploymentInput,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant


def _make_revision_input(**kwargs: object) -> RevisionInput:
    defaults: dict[str, Any] = {
        "image_id": uuid.uuid4(),
        "cluster_mode": ClusterMode.SINGLE_NODE,
        "cluster_size": 1,
        "resource_group": "default",
        "resource_slots": {"cpu": "2", "mem": "4g"},
        "model_vfolder_id": uuid.uuid4(),
        "model_definition_path": "/models/model.yaml",
        "model_definition": ModelDefinition(),
    }
    defaults.update(kwargs)
    return RevisionInput(**defaults)


def _make_create_revision_input_dto(**kwargs: object) -> CreateRevisionInputDTO:
    defaults: dict[str, Any] = {
        "cluster_config": ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
        "resource_config": ResourceConfigInput(
            resource_group=ResourceGroupInput(name="default"),
            resource_slots=ResourceSlotInput(
                entries=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity="2"),
                    ResourceSlotEntryInput(resource_type="mem", quantity="4g"),
                ]
            ),
        ),
        "image": ImageInput(id=uuid.uuid4()),
        "model_runtime_config": ModelRuntimeConfigInput(runtime_variant="custom"),
        "model_mount_config": ModelMountConfigInput(
            vfolder_id=uuid.uuid4(),
            mount_destination="/models",
            definition_path="/models/model.yaml",
        ),
    }
    defaults.update(kwargs)
    return CreateRevisionInputDTO(**defaults)


class TestRevisionInput:
    """Tests for RevisionInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        image_id = uuid.uuid4()
        model_id = uuid.uuid4()
        rev = RevisionInput(
            image_id=image_id,
            cluster_mode=ClusterMode.SINGLE_NODE,
            resource_group="default",
            resource_slots={"cpu": "2"},
            model_vfolder_id=model_id,
            model_definition_path="/models/def.yaml",
            model_definition=ModelDefinition(),
        )
        assert rev.image_id == image_id
        assert rev.cluster_mode == ClusterMode.SINGLE_NODE
        assert rev.resource_group == "default"
        assert rev.model_vfolder_id == model_id
        assert rev.model_definition_path == "/models/def.yaml"

    def test_default_cluster_size_is_one(self) -> None:
        rev = _make_revision_input()
        assert rev.cluster_size == 1

    def test_default_runtime_variant_is_custom(self) -> None:
        rev = _make_revision_input()
        assert rev.runtime_variant == RuntimeVariant.CUSTOM

    def test_default_model_mount_destination(self) -> None:
        rev = _make_revision_input()
        assert rev.model_mount_destination == "/models"

    def test_optional_name_defaults_to_none(self) -> None:
        rev = _make_revision_input()
        assert rev.name is None

    def test_optional_extra_mounts_defaults_to_none(self) -> None:
        rev = _make_revision_input()
        assert rev.extra_mounts is None

    def test_optional_environ_defaults_to_none(self) -> None:
        rev = _make_revision_input()
        assert rev.environ is None

    def test_cluster_size_must_be_at_least_one(self) -> None:
        with pytest.raises(ValidationError):
            _make_revision_input(cluster_size=0)

    def test_with_extra_mounts(self) -> None:
        mount = ExtraVFolderMountInput(vfolder_id=uuid.uuid4(), mount_destination="/data")
        rev = _make_revision_input(extra_mounts=[mount])
        assert rev.extra_mounts is not None
        assert len(rev.extra_mounts) == 1
        assert rev.extra_mounts[0].mount_destination == "/data"

    def test_with_vllm_runtime_variant(self) -> None:
        rev = _make_revision_input(runtime_variant=RuntimeVariant.VLLM)
        assert rev.runtime_variant == RuntimeVariant.VLLM


class TestExtraVFolderMountInput:
    """Tests for ExtraVFolderMountInput model."""

    def test_valid_creation(self) -> None:
        vfolder_id = uuid.uuid4()
        mount = ExtraVFolderMountInput(vfolder_id=vfolder_id, mount_destination="/data")
        assert mount.vfolder_id == vfolder_id
        assert mount.mount_destination == "/data"

    def test_mount_destination_defaults_to_none(self) -> None:
        mount = ExtraVFolderMountInput(vfolder_id=uuid.uuid4())
        assert mount.mount_destination is None

    def test_missing_vfolder_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ExtraVFolderMountInput.model_validate({})


class TestRollingUpdateConfigInput:
    """Tests for RollingUpdateConfigInput model."""

    def test_valid_creation(self) -> None:
        config = RollingUpdateConfigInput(max_surge=2, max_unavailable=1)
        assert config.max_surge == 2
        assert config.max_unavailable == 1

    def test_defaults(self) -> None:
        config = RollingUpdateConfigInput()
        assert config.max_surge == 1
        assert config.max_unavailable == 0

    def test_negative_max_surge_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            RollingUpdateConfigInput(max_surge=-1)

    def test_negative_max_unavailable_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            RollingUpdateConfigInput(max_unavailable=-1)


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
        with pytest.raises(ValidationError):
            BlueGreenConfigInput(promote_delay_seconds=-1)


class TestCreateDeploymentInput:
    """Tests for CreateDeploymentInput model creation and validation."""

    def _make_metadata(self, **kwargs: object) -> ModelDeploymentMetadataInput:
        defaults: dict[str, Any] = {
            "project_id": uuid.uuid4(),
            "domain_name": "default",
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
            "desired_replica_count": 2,
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
        assert inp.desired_replica_count == 2

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
        with pytest.raises(ValidationError):
            self._make_input(
                metadata=self._make_metadata(name="   "),
            )

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            self._make_input(
                metadata=self._make_metadata(name=""),
            )

    def test_desired_replica_count_zero_is_valid(self) -> None:
        inp = self._make_input(desired_replica_count=0)
        assert inp.desired_replica_count == 0

    def test_negative_replica_count_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            self._make_input(desired_replica_count=-1)

    def test_blue_green_strategy(self) -> None:
        inp = self._make_input(
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.BLUE_GREEN,
            ),
        )
        assert inp.default_deployment_strategy.type == DeploymentStrategy.BLUE_GREEN

    def test_with_rolling_update_config(self) -> None:
        rolling = RollingUpdateConfigInput(max_surge=2, max_unavailable=1)
        inp = self._make_input(
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
                rolling_update=rolling,
            ),
        )
        assert inp.default_deployment_strategy.rolling_update is not None
        assert inp.default_deployment_strategy.rolling_update.max_surge == 2

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
        image_id = uuid.uuid4()
        rev = _make_create_revision_input_dto(image=ImageInput(id=image_id))
        inp = self._make_input(initial_revision=rev)
        assert inp.initial_revision.image.id == image_id

    def test_missing_metadata_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateDeploymentInput.model_validate({
                "network_access": {},
                "default_deployment_strategy": {"type": "ROLLING"},
                "desired_replica_count": 1,
            })


class TestUpdateDeploymentInput:
    """Tests for UpdateDeploymentInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        inp = UpdateDeploymentInput(name=None, desired_replica_count=None, tags=None)
        assert inp.name is None
        assert inp.desired_replica_count is None
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
        with pytest.raises(ValidationError):
            UpdateDeploymentInput(name="   ")

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDeploymentInput(name="")

    def test_desired_replicas_zero_is_valid(self) -> None:
        inp = UpdateDeploymentInput(desired_replica_count=0)
        assert inp.desired_replica_count == 0

    def test_negative_replicas_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDeploymentInput(desired_replica_count=-1)

    def test_partial_update_name_only(self) -> None:
        inp = UpdateDeploymentInput(name="updated-name")
        assert inp.name == "updated-name"
        assert inp.desired_replica_count is None


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
        with pytest.raises(ValidationError):
            DeleteDeploymentInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
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
        with pytest.raises(ValidationError):
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
        with pytest.raises(ValidationError):
            ScaleDeploymentInput(id=uuid.uuid4(), replicas=-1)

    def test_missing_replicas_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ScaleDeploymentInput.model_validate({"id": str(uuid.uuid4())})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ScaleDeploymentInput.model_validate({"replicas": 3})


class TestAddRevisionInput:
    """Tests for AddRevisionInput model creation and validation."""

    def test_valid_creation(self) -> None:
        deployment_id = uuid.uuid4()
        rev = _make_revision_input()
        inp = AddRevisionInput(deployment_id=deployment_id, revision=rev)
        assert inp.deployment_id == deployment_id
        assert inp.revision.cluster_mode == ClusterMode.SINGLE_NODE

    def test_missing_deployment_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AddRevisionInput.model_validate({"revision": {}})

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        rev = _make_revision_input()
        inp = AddRevisionInput(deployment_id=deployment_id, revision=rev)
        json_str = inp.model_dump_json()
        restored = AddRevisionInput.model_validate_json(json_str)
        assert restored.deployment_id == deployment_id
        assert restored.revision.cluster_mode == ClusterMode.SINGLE_NODE
