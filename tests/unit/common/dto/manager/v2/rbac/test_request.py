"""Tests for ai.backend.common.dto.manager.v2.rbac.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreateRoleInput,
    DeleteRoleInput,
    PurgeRoleInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.types import ScopeInputDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET, Unset

_SCOPE = ScopeInputDTO(scope_type=EntityType("project"), scope_id=str(uuid.uuid4()))


class TestCreateRoleInput:
    """Tests for CreateRoleInput model creation and validation."""

    def test_the_scope_is_read_off_the_scope_field(self) -> None:
        req = CreateRoleInput(name="Admin", scope=_SCOPE)
        assert req.scope_input() == _SCOPE

    def test_the_deprecated_scopes_field_carries_one_scope(self) -> None:
        req = CreateRoleInput(name="Admin", scopes=[_SCOPE])
        assert req.scope_input() == _SCOPE

    def test_missing_scope_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="Admin")
        with pytest.raises(ValidationError):
            CreateRoleInput(name="Admin", scopes=[])

    def test_more_than_one_scope_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="Admin", scopes=[_SCOPE, _SCOPE])

    def test_scope_and_scopes_together_raise_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateRoleInput(name="Admin", scope=_SCOPE, scopes=[_SCOPE])

    def test_valid_creation_with_name_and_source(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="Admin")
        assert req.name == "Admin"
        assert req.description is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateRoleInput(
            scope=_SCOPE,
            name="Developer",
            description="Developer role",
        )
        assert req.name == "Developer"
        assert req.description == "Developer role"

    def test_a_source_is_not_carried(self) -> None:
        req = CreateRoleInput.model_validate({"scope": _SCOPE, "name": "Admin", "source": "system"})
        assert not hasattr(req, "source")

    def test_default_description_is_none(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="MyRole")
        assert req.description is None

    def test_name_whitespace_is_stripped(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="  Admin  ")
        assert req.name == "Admin"

    def test_name_with_leading_whitespace_stripped(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="  Role")
        assert req.name == "Role"

    def test_name_with_trailing_whitespace_stripped(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="Role  ")
        assert req.name == "Role"


class TestCreateRoleInputValidationFailures:
    """Tests for CreateRoleInput validation failures."""

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput(scope=_SCOPE, name="")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput(scope=_SCOPE, name="   ")

    def test_tab_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput(scope=_SCOPE, name="\t")

    def test_newline_only_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput(scope=_SCOPE, name="\n")

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput(scope=_SCOPE, name="a" * 257)

    def test_name_at_max_length_is_valid(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="a" * 256)
        assert len(req.name) == 256

    def test_name_at_min_length_is_valid(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="a")
        assert req.name == "a"

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateRoleInput.model_validate({})


class TestUpdateRoleInput:
    """Tests for UpdateRoleInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        req = UpdateRoleInput(name=None, description=None, status=None, auto_assign=None)
        assert req.name is None
        assert req.description is None
        assert req.status is None
        assert req.auto_assign is None

    def test_all_fields_default_to_unset(self) -> None:
        req = UpdateRoleInput()
        assert req.name is UNSET
        assert req.description is UNSET
        assert req.status is UNSET
        assert req.auto_assign is UNSET

    def test_default_description_is_unset(self) -> None:
        req = UpdateRoleInput()
        assert req.description is UNSET
        assert isinstance(req.description, Unset)

    def test_explicit_unset_description_signals_no_change(self) -> None:
        req = UpdateRoleInput(description=UNSET)
        assert req.description is UNSET
        assert isinstance(req.description, Unset)

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
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateRoleInput(name="   ")

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
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
        assert req.status is UNSET

    def test_partial_update_status_only(self) -> None:
        req = UpdateRoleInput(status=RoleStatus.INACTIVE)
        assert req.name is UNSET
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
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteRoleInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
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
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            PurgeRoleInput.model_validate({"id": "invalid-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            PurgeRoleInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        role_id = uuid.uuid4()
        req = PurgeRoleInput(id=role_id)
        assert isinstance(req.id, uuid.UUID)


class TestCreateRoleInputRoundTrip:
    """Tests for CreateRoleInput serialization round-trip."""

    def test_round_trip_with_all_fields(self) -> None:
        req = CreateRoleInput(
            scope=_SCOPE,
            name="Admin",
            description="Admin role",
        )
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.description == req.description

    def test_round_trip_with_minimal_fields(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="Admin")
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.description is None

    def test_round_trip_with_system_source(self) -> None:
        req = CreateRoleInput(scope=_SCOPE, name="SystemRole")
        json_data = req.model_dump_json()
        restored = CreateRoleInput.model_validate_json(json_data)
        assert restored.name == req.name


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
    """Tests for UpdateRoleInput serialization round-trip (non-UNSET values)."""

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
