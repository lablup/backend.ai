"""Tests for ai.backend.common.dto.manager.v2.model_serving.request module."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.model_serving.request import (
    CreateServiceInput,
    DeleteServiceInput,
    GenerateTokenInput,
    ScaleServiceInput,
    ServiceConfigInput,
    UpdateServiceInput,
)
from ai.backend.common.types import RuntimeVariant


def _make_service_config(**kwargs: object) -> ServiceConfigInput:
    defaults: dict[str, Any] = {
        "model": "my-model",
        "scaling_group": "default",
    }
    defaults.update(kwargs)
    return ServiceConfigInput(**defaults)


def _make_create_input(**kwargs: object) -> CreateServiceInput:
    defaults: dict[str, Any] = {
        "service_name": "my-service",
        "replicas": 2,
        "config": _make_service_config(),
    }
    defaults.update(kwargs)
    return CreateServiceInput(**defaults)


class TestServiceConfigInput:
    """Tests for ServiceConfigInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        config = ServiceConfigInput(model="my-model", scaling_group="default")
        assert config.model == "my-model"
        assert config.scaling_group == "default"

    def test_model_definition_path_defaults_to_none(self) -> None:
        config = _make_service_config()
        assert config.model_definition_path is None

    def test_model_mount_destination_defaults_to_models(self) -> None:
        config = _make_service_config()
        assert config.model_mount_destination == "/models"

    def test_extra_mounts_defaults_to_empty_dict(self) -> None:
        config = _make_service_config()
        assert config.extra_mounts == {}

    def test_environ_defaults_to_none(self) -> None:
        config = _make_service_config()
        assert config.environ is None

    def test_resources_defaults_to_none(self) -> None:
        config = _make_service_config()
        assert config.resources is None

    def test_resource_opts_defaults_to_empty_dict(self) -> None:
        config = _make_service_config()
        assert config.resource_opts == {}

    def test_with_extra_mounts(self) -> None:
        mount_id = uuid.uuid4()
        config = _make_service_config(extra_mounts={mount_id: {"path": "/data"}})
        assert mount_id in config.extra_mounts

    def test_with_resources(self) -> None:
        config = _make_service_config(resources={"cpu": "2", "mem": 4})
        assert config.resources is not None
        assert config.resources["cpu"] == "2"

    def test_with_fractional_resource_values(self) -> None:
        config = _make_service_config(resources={"cpu": 4, "mem": "32g", "cuda.shares": 2.5})
        assert config.resources is not None
        assert config.resources["cuda.shares"] == 2.5

    def test_negative_float_resource_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"greater than or equal to 0"):
            _make_service_config(resources={"cuda.shares": -0.5})

    def test_missing_model_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ServiceConfigInput.model_validate({"scaling_group": "default"})

    def test_missing_scaling_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ServiceConfigInput.model_validate({"model": "my-model"})


class TestCreateServiceInput:
    """Tests for CreateServiceInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        inp = _make_create_input()
        assert inp.service_name == "my-service"
        assert inp.replicas == 2

    def test_service_name_with_whitespace_fails_pattern(self) -> None:
        # pattern constraint runs before field_validator, so whitespace-padded names fail
        with pytest.raises(ValidationError):
            _make_create_input(service_name="  my-service  ")

    def test_service_name_min_length_4(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_name="abc")

    def test_service_name_max_length_64(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_name="a" * 65)

    def test_service_name_at_min_length_is_valid(self) -> None:
        inp = _make_create_input(service_name="abcd")
        assert inp.service_name == "abcd"

    def test_service_name_at_max_length_is_valid(self) -> None:
        inp = _make_create_input(service_name="a" * 64)
        assert len(inp.service_name) == 64

    def test_service_name_pattern_valid(self) -> None:
        inp = _make_create_input(service_name="my-service-01")
        assert inp.service_name == "my-service-01"

    def test_service_name_pattern_invalid_starts_with_hyphen(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_name="-invalid")

    def test_service_name_pattern_invalid_ends_with_hyphen(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_name="invalid-")

    def test_replicas_must_be_at_least_one(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(replicas=0)

    def test_default_group_name(self) -> None:
        inp = _make_create_input()
        assert inp.group_name == "default"

    def test_default_domain_name(self) -> None:
        inp = _make_create_input()
        assert inp.domain_name == "default"

    def test_default_runtime_variant_is_custom(self) -> None:
        inp = _make_create_input()
        assert inp.runtime_variant == RuntimeVariant("custom")

    def test_default_cluster_size_is_one(self) -> None:
        inp = _make_create_input()
        assert inp.cluster_size == 1

    def test_default_cluster_mode(self) -> None:
        inp = _make_create_input()
        assert inp.cluster_mode == "SINGLE_NODE"

    def test_default_open_to_public_is_false(self) -> None:
        inp = _make_create_input()
        assert inp.open_to_public is False

    def test_image_defaults_to_none(self) -> None:
        inp = _make_create_input()
        assert inp.image is None

    def test_architecture_defaults_to_none(self) -> None:
        inp = _make_create_input()
        assert inp.architecture is None

    def test_with_vllm_runtime(self) -> None:
        inp = _make_create_input(runtime_variant=RuntimeVariant("vllm"))
        assert inp.runtime_variant == RuntimeVariant("vllm")

    def test_nested_config_accessible(self) -> None:
        config = _make_service_config(model="bert-model")
        inp = _make_create_input(config=config)
        assert inp.config.model == "bert-model"

    def test_missing_service_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateServiceInput.model_validate({"replicas": 2, "config": {}})

    def test_round_trip(self) -> None:
        inp = _make_create_input(service_name="my-service", replicas=3)
        json_str = inp.model_dump_json()
        restored = CreateServiceInput.model_validate_json(json_str)
        assert restored.service_name == "my-service"
        assert restored.replicas == 3
        assert restored.config.model == "my-model"


class TestUpdateServiceInput:
    """Tests for UpdateServiceInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        inp = UpdateServiceInput(name=None, replicas=None)
        assert inp.name is None
        assert inp.replicas is None

    def test_name_update(self) -> None:
        inp = UpdateServiceInput(name="new-name")
        assert inp.name == "new-name"

    def test_replicas_update(self) -> None:
        inp = UpdateServiceInput(replicas=5)
        assert inp.replicas == 5

    def test_replicas_zero_is_valid(self) -> None:
        inp = UpdateServiceInput(replicas=0)
        assert inp.replicas == 0

    def test_negative_replicas_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateServiceInput(replicas=-1)

    def test_default_all_none(self) -> None:
        inp = UpdateServiceInput()
        assert inp.name is None
        assert inp.replicas is None

    def test_round_trip(self) -> None:
        inp = UpdateServiceInput(name="updated-name", replicas=3)
        json_str = inp.model_dump_json()
        restored = UpdateServiceInput.model_validate_json(json_str)
        assert restored.name == "updated-name"
        assert restored.replicas == 3


class TestDeleteServiceInput:
    """Tests for DeleteServiceInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        service_id = uuid.uuid4()
        inp = DeleteServiceInput(id=service_id)
        assert inp.id == service_id

    def test_valid_creation_from_uuid_string(self) -> None:
        service_id = uuid.uuid4()
        inp = DeleteServiceInput.model_validate({"id": str(service_id)})
        assert inp.id == service_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteServiceInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteServiceInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        inp = DeleteServiceInput(id=uuid.uuid4())
        assert isinstance(inp.id, uuid.UUID)

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        inp = DeleteServiceInput(id=service_id)
        json_str = inp.model_dump_json()
        restored = DeleteServiceInput.model_validate_json(json_str)
        assert restored.id == service_id


class TestScaleServiceInput:
    """Tests for ScaleServiceInput model creation and validation."""

    def test_valid_creation(self) -> None:
        inp = ScaleServiceInput(to=3)
        assert inp.to == 3

    def test_zero_is_valid(self) -> None:
        inp = ScaleServiceInput(to=0)
        assert inp.to == 0

    def test_negative_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ScaleServiceInput(to=-1)

    def test_missing_to_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ScaleServiceInput.model_validate({})

    def test_round_trip(self) -> None:
        inp = ScaleServiceInput(to=5)
        json_str = inp.model_dump_json()
        restored = ScaleServiceInput.model_validate_json(json_str)
        assert restored.to == 5


class TestGenerateTokenInput:
    """Tests for GenerateTokenInput model creation and validation."""

    def test_default_all_none(self) -> None:
        inp = GenerateTokenInput()
        assert inp.duration is None
        assert inp.valid_until is None

    def test_with_duration(self) -> None:
        inp = GenerateTokenInput(duration="1h")
        assert inp.duration == "1h"

    def test_with_valid_until(self) -> None:
        inp = GenerateTokenInput(valid_until=1700000000)
        assert inp.valid_until == 1700000000

    def test_with_both_fields(self) -> None:
        inp = GenerateTokenInput(duration="30m", valid_until=1700000000)
        assert inp.duration == "30m"
        assert inp.valid_until == 1700000000

    def test_round_trip_with_duration(self) -> None:
        inp = GenerateTokenInput(duration="2h")
        json_str = inp.model_dump_json()
        restored = GenerateTokenInput.model_validate_json(json_str)
        assert restored.duration == "2h"
        assert restored.valid_until is None
