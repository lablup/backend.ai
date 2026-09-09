"""Tests for ai.backend.common.dto.manager.v2.resource_group.request module."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.resource_group.request import (
    CreateResourceGroupInput,
    DeleteResourceGroupInput,
    ResourceWeightEntryInput,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET, Unset


class TestCreateResourceGroupInput:
    """Tests for CreateResourceGroupInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateResourceGroupInput(name="my-group", domain_name="default")
        assert req.name == "my-group"
        assert req.domain_name == "default"
        assert req.description is None
        assert req.total_resource_slots is None
        assert req.allowed_vfolder_hosts is None
        assert req.integration_name is None
        assert req.resource_policy is None
        assert req.is_default is False

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateResourceGroupInput(
            name="my-group",
            domain_name="default",
            description="A test group",
            total_resource_slots={"cpu": "4"},
            allowed_vfolder_hosts={"default": "rw"},
            integration_name="ext-001",
            resource_policy="default",
            is_default=True,
        )
        assert req.name == "my-group"
        assert req.description == "A test group"
        assert req.total_resource_slots == {"cpu": "4"}
        assert req.is_default is True

    def test_name_whitespace_is_stripped(self) -> None:
        req = CreateResourceGroupInput(name="  my-group  ", domain_name="default")
        assert req.name == "my-group"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateResourceGroupInput(name="", domain_name="default")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateResourceGroupInput(name="   ", domain_name="default")

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateResourceGroupInput(name="a" * 257, domain_name="default")

    def test_name_at_max_length_is_valid(self) -> None:
        req = CreateResourceGroupInput(name="a" * 256, domain_name="default")
        assert len(req.name) == 256

    def test_missing_domain_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateResourceGroupInput.model_validate({"name": "my-group"})

    def test_round_trip(self) -> None:
        req = CreateResourceGroupInput(name="my-group", domain_name="default")
        json_data = req.model_dump_json()
        restored = CreateResourceGroupInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.domain_name == req.domain_name


class TestUpdateResourceGroupInput:
    """Tests for UpdateResourceGroupInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        req = UpdateResourceGroupInput(
            name=None,
            is_active=None,
        )
        assert req.name is None
        assert req.is_active is None

    def test_default_unset_fields(self) -> None:
        req = UpdateResourceGroupInput()
        assert req.name is UNSET
        assert req.is_active is UNSET
        assert req.is_default is UNSET
        assert req.description is UNSET
        assert isinstance(req.description, Unset)
        assert req.total_resource_slots is UNSET
        assert req.allowed_vfolder_hosts is UNSET
        assert req.integration_name is UNSET
        assert req.resource_policy is UNSET

    def test_unset_description_means_no_change(self) -> None:
        req = UpdateResourceGroupInput(description=UNSET)
        assert req.description is UNSET

    def test_none_description_signals_clear(self) -> None:
        req = UpdateResourceGroupInput(description=None)
        assert req.description is None

    def test_name_update(self) -> None:
        req = UpdateResourceGroupInput(name="new-name")
        assert req.name == "new-name"

    def test_is_active_update(self) -> None:
        req = UpdateResourceGroupInput(is_active=False)
        assert req.is_active is False

    def test_total_resource_slots_update(self) -> None:
        req = UpdateResourceGroupInput(total_resource_slots={"cpu": "8"})
        assert req.total_resource_slots == {"cpu": "8"}

    def test_round_trip_with_all_none(self) -> None:
        req = UpdateResourceGroupInput(
            name=None,
            description=None,
            is_active=None,
            total_resource_slots=None,
            allowed_vfolder_hosts=None,
            integration_name=None,
            resource_policy=None,
        )
        json_data = req.model_dump_json()
        restored = UpdateResourceGroupInput.model_validate_json(json_data)
        assert restored.name is None
        assert restored.description is None

    def test_omitted_fields_survive_round_trip(self) -> None:
        req = UpdateResourceGroupInput(is_active=True)
        restored = UpdateResourceGroupInput.model_validate_json(req.model_dump_json())
        assert restored.is_active is True
        assert restored.name is UNSET
        assert restored.description is UNSET


class TestUpdateResourceGroupFairShareSpecInput:
    """Tests for UpdateResourceGroupFairShareSpecInput omitted-vs-null semantics."""

    def test_default_unset_fields(self) -> None:
        req = UpdateResourceGroupFairShareSpecInput(resource_group_name="rg")
        assert req.half_life_days is UNSET
        assert req.lookback_days is UNSET
        assert req.decay_unit_days is UNSET
        assert req.default_weight is UNSET
        assert req.resource_weights is UNSET

    def test_none_stays_none(self) -> None:
        req = UpdateResourceGroupFairShareSpecInput(
            resource_group_name="rg",
            half_life_days=None,
            resource_weights=None,
        )
        assert req.half_life_days is None
        assert req.resource_weights is None
        assert req.lookback_days is UNSET

    def test_value_update(self) -> None:
        req = UpdateResourceGroupFairShareSpecInput(
            resource_group_name="rg",
            half_life_days=14,
            resource_weights=[ResourceWeightEntryInput(resource_type="cpu", weight=Decimal("2"))],
        )
        assert req.half_life_days == 14
        assert req.resource_weights is not None
        assert not isinstance(req.resource_weights, Unset)
        assert req.resource_weights[0].resource_type == "cpu"


class TestUpdateResourceGroupConfigInput:
    """Tests for UpdateResourceGroupConfigInput omitted-vs-null semantics."""

    def test_default_unset_fields(self) -> None:
        req = UpdateResourceGroupConfigInput(resource_group_name="rg")
        assert req.is_active is UNSET
        assert req.is_public is UNSET
        assert req.is_default is UNSET
        assert req.description is UNSET
        assert req.app_proxy_addr is UNSET
        assert req.appproxy_api_token is UNSET
        assert req.use_host_network is UNSET
        assert req.scheduler_type is UNSET
        assert req.preemption is UNSET

    def test_none_stays_none(self) -> None:
        req = UpdateResourceGroupConfigInput(
            resource_group_name="rg",
            description=None,
            app_proxy_addr=None,
            preemption=None,
        )
        assert req.description is None
        assert req.app_proxy_addr is None
        assert req.preemption is None
        assert req.appproxy_api_token is UNSET

    def test_omitted_fields_survive_json_round_trip(self) -> None:
        req = UpdateResourceGroupConfigInput.model_validate_json(
            '{"resource_group_name": "rg", "is_active": false, "description": null}'
        )
        assert req.is_active is False
        assert req.description is None
        assert req.is_public is UNSET
        assert req.scheduler_type is UNSET


class TestDeleteResourceGroupInput:
    """Tests for DeleteResourceGroupInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteResourceGroupInput(id=group_id)
        assert req.id == group_id

    def test_valid_creation_from_uuid_string(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteResourceGroupInput.model_validate({"id": str(group_id)})
        assert req.id == group_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteResourceGroupInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteResourceGroupInput.model_validate({})

    def test_round_trip(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteResourceGroupInput(id=group_id)
        json_data = req.model_dump_json()
        restored = DeleteResourceGroupInput.model_validate_json(json_data)
        assert restored.id == req.id
