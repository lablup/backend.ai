"""Tests for ai.backend.common.dto.manager.v2.rbac.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.permission.types import RoleSource, RoleStatus
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreateRoleInput,
    DeleteRoleInput,
    PurgeRoleInput,
    UpdateRoleInput,
)


class TestCreateRoleInput:
    """Tests for CreateRoleInput model creation and validation."""

    def test_valid_creation_with_name_and_source(self) -> None:
        req = CreateRoleInput(name="Admin", source=RoleSource.CUSTOM)
        assert req.name == "Admin"
        assert req.source == RoleSource.CUSTOM
        assert req.description is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateRoleInput(
            name="Developer",
            description="Developer role",
            source=RoleSource.CUSTOM,
        )
        assert req.name == "Developer"
        assert req.description == "Developer role"
        assert req.source == RoleSource.CUSTOM

    def test_valid_creation_with_system_source(self) -> None:
        req = CreateRoleInput(name="SystemAdmin", source=RoleSource.SYSTEM)
        assert req.name == "SystemAdmin"
        assert req.source == RoleSource.SYSTEM

    def test_default_source_is_custom(self) -> None:
        req = CreateRoleInput(name="MyRole")
        assert req.source == RoleSource.CUSTOM

    def test_default_description_is_none(self) -> None:
        req = CreateRoleInput(name="MyRole")
        assert req.description is None

    def test_name_whitespace_is_stripped(self) -> None:
        req = CreateRoleInput(name="  Admin  ")
        assert req.name == "Admin"

    def test_name_with_leading_whitespace_stripped(self) -> None:
        req = CreateRoleInput(name="  Role")
        assert req.name == "Role"

    def test_name_with_trailing_whitespace_stripped(self) -> None:
        req = CreateRoleInput(name="Role  ")
        assert req.name == "Role"


class TestCreateRoleInputValidationFailures:
    """Tests for CreateRoleInput validation failures."""

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="   ")

    def test_tab_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="\t")

    def test_newline_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="\n")

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="a" * 257)

    def test_name_at_max_length_is_valid(self) -> None:
        req = CreateRoleInput(name="a" * 256)
        assert len(req.name) == 256

    def test_name_at_min_length_is_valid(self) -> None:
        req = CreateRoleInput(name="a")
        assert req.name == "a"

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput.model_validate({})


class TestUpdateRoleInput:
    """Tests for UpdateRoleInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        req = UpdateRoleInput(name=None, description=None, status=None)
        assert req.name is None
        assert req.description is None
        assert req.status is None

    def test_default_description_is_sentinel(self) -> None:
        req = UpdateRoleInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)

    def test_explicit_sentinel_description_signals_clear(self) -> None:
        req = UpdateRoleInput(description=SENTINEL)
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)

    def test_none_description_means_no_change(self) -> None:
        req = UpdateRoleInput(description=None)
        assert req.description is None

    def test_string_description_update(self) -> None:
        req = UpdateRoleInput(description="New description")
        assert req.description == "New description"

    def test_name_update(self) -> None:
        req = UpdateRoleInput(name="NewName")
        assert req.name == "NewName"

    def test_name_whitespace_is_stripped(self) -> None:
        req = UpdateRoleInput(name="  NewName  ")
        assert req.name == "NewName"

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateRoleInput(name="   ")

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateRoleInput(name="")

    def test_status_update(self) -> None:
        req = UpdateRoleInput(status=RoleStatus.INACTIVE)
        assert req.status == RoleStatus.INACTIVE

    def test_status_update_to_active(self) -> None:
        req = UpdateRoleInput(status=RoleStatus.ACTIVE)
        assert req.status == RoleStatus.ACTIVE

    def test_partial_update_name_only(self) -> None:
        req = UpdateRoleInput(name="UpdatedName")
        assert req.name == "UpdatedName"
        assert req.status is None

    def test_partial_update_status_only(self) -> None:
        req = UpdateRoleInput(status=RoleStatus.INACTIVE)
        assert req.name is None
        assert req.status == RoleStatus.INACTIVE


class TestDeleteRoleInput:
    """Tests for DeleteRoleInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        role_id = uuid.uuid4()
        req = DeleteRoleInput(id=role_id)
        assert req.id == role_id

    def test_valid_creation_from_uuid_string(self) -> None:
        role_id = uuid.uuid4()
        req = DeleteRoleInput.model_validate({"id": str(role_id)})
        assert req.id == role_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteRoleInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteRoleInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        role_id = uuid.uuid4()
        req = DeleteRoleInput(id=role_id)
        assert isinstance(req.id, uuid.UUID)


class TestPurgeRoleInput:
    """Tests for PurgeRoleInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        role_id = uuid.uuid4()
        req = PurgeRoleInput(id=role_id)
        assert req.id == role_id

    def test_valid_creation_from_uuid_string(self) -> None:
        role_id = uuid.uuid4()
        req = PurgeRoleInput.model_validate({"id": str(role_id)})
        assert req.id == role_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PurgeRoleInput.model_validate({"id": "invalid-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PurgeRoleInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        role_id = uuid.uuid4()
        req = PurgeRoleInput(id=role_id)
        assert isinstance(req.id, uuid.UUID)


class TestCreateRoleInputRoundTrip:
    """Tests for CreateRoleInput serialization round-trip."""

    def test_round_trip_with_all_fields(self) -> None:
        req = CreateRoleInput(
            name="Admin",
            description="Admin role",
            source=RoleSource.CUSTOM,
        )
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.description == req.description
        assert restored.source == req.source

    def test_round_trip_with_minimal_fields(self) -> None:
        req = CreateRoleInput(name="Admin")
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.description is None
        assert restored.source == RoleSource.CUSTOM

    def test_round_trip_with_system_source(self) -> None:
        req = CreateRoleInput(name="SystemRole", source=RoleSource.SYSTEM)
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.source == req.source


class TestDeleteRoleInputRoundTrip:
    """Tests for DeleteRoleInput serialization round-trip."""

    def test_round_trip(self) -> None:
        role_id = uuid.uuid4()
        req = DeleteRoleInput(id=role_id)
        json_data = req.model_dump_json()
        restored = DeleteRoleInput.model_validate_json(json_data)
        assert restored.id == req.id


class TestPurgeRoleInputRoundTrip:
    """Tests for PurgeRoleInput serialization round-trip."""

    def test_round_trip(self) -> None:
        role_id = uuid.uuid4()
        req = PurgeRoleInput(id=role_id)
        json_data = req.model_dump_json()
        restored = PurgeRoleInput.model_validate_json(json_data)
        assert restored.id == req.id


class TestUpdateRoleInputRoundTrip:
    """Tests for UpdateRoleInput serialization round-trip (non-SENTINEL values)."""

    def test_round_trip_with_all_none(self) -> None:
        req = UpdateRoleInput(name=None, description=None, status=None)
        json_data = req.model_dump_json()
        restored = UpdateRoleInput.model_validate_json(json_data)
        assert restored.name is None
        assert restored.description is None
        assert restored.status is None

    def test_round_trip_with_name_and_status(self) -> None:
        req = UpdateRoleInput(name="Updated", status=RoleStatus.ACTIVE, description=None)
        json_data = req.model_dump_json()
        restored = UpdateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.status == req.status
        assert restored.description is None

    def test_round_trip_with_description_string(self) -> None:
        req = UpdateRoleInput(description="New description", name=None, status=None)
        json_data = req.model_dump_json()
        restored = UpdateRoleInput.model_validate_json(json_data)
        assert restored.description == "New description"
