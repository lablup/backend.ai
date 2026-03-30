"""Tests for ai.backend.common.dto.manager.v2.resource_group.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.resource_group.request import (
    CreateResourceGroupInput,
    DeleteResourceGroupInput,
    UpdateResourceGroupInput,
)


class TestCreateResourceGroupInput:
    """Tests for CreateResourceGroupInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateResourceGroupInput(name="my-group", domain_name="default")
        assert req.name == "my-group"
        assert req.domain_name == "default"
        assert req.description is None
        assert req.total_resource_slots is None
        assert req.allowed_vfolder_hosts is None
        assert req.integration_id is None
        assert req.resource_policy is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateResourceGroupInput(
            name="my-group",
            domain_name="default",
            description="A test group",
            total_resource_slots={"cpu": "4"},
            allowed_vfolder_hosts={"default": "rw"},
            integration_id="ext-001",
            resource_policy="default",
        )
        assert req.name == "my-group"
        assert req.description == "A test group"
        assert req.total_resource_slots == {"cpu": "4"}

    def test_name_whitespace_is_stripped(self) -> None:
        req = CreateResourceGroupInput(name="  my-group  ", domain_name="default")
        assert req.name == "my-group"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupInput(name="", domain_name="default")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupInput(name="   ", domain_name="default")

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupInput(name="a" * 257, domain_name="default")

    def test_name_at_max_length_is_valid(self) -> None:
        req = CreateResourceGroupInput(name="a" * 256, domain_name="default")
        assert len(req.name) == 256

    def test_missing_domain_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
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

    def test_default_sentinel_fields(self) -> None:
        req = UpdateResourceGroupInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)
        assert req.total_resource_slots is SENTINEL
        assert req.allowed_vfolder_hosts is SENTINEL
        assert req.integration_id is SENTINEL
        assert req.resource_policy is SENTINEL

    def test_sentinel_description_signals_clear(self) -> None:
        req = UpdateResourceGroupInput(description=SENTINEL)
        assert req.description is SENTINEL

    def test_none_description_means_no_change(self) -> None:
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
            integration_id=None,
            resource_policy=None,
        )
        json_data = req.model_dump_json()
        restored = UpdateResourceGroupInput.model_validate_json(json_data)
        assert restored.name is None
        assert restored.description is None


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
        with pytest.raises(ValidationError):
            DeleteResourceGroupInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteResourceGroupInput.model_validate({})

    def test_round_trip(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteResourceGroupInput(id=group_id)
        json_data = req.model_dump_json()
        restored = DeleteResourceGroupInput.model_validate_json(json_data)
        assert restored.id == req.id
