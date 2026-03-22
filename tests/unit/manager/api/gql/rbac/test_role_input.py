"""Unit tests for UpdateRoleInput.to_pydantic()."""

from __future__ import annotations

import uuid

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.dto.manager.v2.rbac.request import UpdateRoleInput as UpdateRoleInputDTO
from ai.backend.manager.api.gql.rbac.types.role import RoleStatusGQL, UpdateRoleInput


class TestUpdateRoleInputToPydantic:
    """Tests for UpdateRoleInput.to_pydantic() method."""

    def test_description_with_none_produces_none_in_dto(self) -> None:
        """UpdateRoleInput with description=None → dto.description is None (clear)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            description=None,
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.description is None

    def test_description_with_unset_produces_sentinel_in_dto(self) -> None:
        """UpdateRoleInput with description=UNSET → dto.description is SENTINEL (no change)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # description is omitted (UNSET by default)
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.description is SENTINEL

    def test_description_with_string_produces_string_in_dto(self) -> None:
        """UpdateRoleInput with description="text" → dto.description == "text"."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            description="some text",
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.description == "some text"

    def test_name_with_unset_produces_none_in_dto(self) -> None:
        """UpdateRoleInput with name=UNSET → dto.name is None (no change)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # name is omitted (UNSET by default)
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.name is None

    def test_name_with_string_produces_string_in_dto(self) -> None:
        """UpdateRoleInput with name="new name" → dto.name == "new name"."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            name="new name",
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.name == "new name"

    def test_status_with_unset_produces_none_in_dto(self) -> None:
        """UpdateRoleInput with status=UNSET → dto.status is None (no change)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # status is omitted (UNSET by default)
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.status is None

    def test_status_with_active_produces_role_status_active(self) -> None:
        """UpdateRoleInput with status=RoleStatusGQL.ACTIVE → dto.status == RoleStatus.ACTIVE."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            status=RoleStatusGQL.ACTIVE,
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.status == RoleStatus.ACTIVE

    def test_status_with_inactive_produces_role_status_inactive(self) -> None:
        """UpdateRoleInput with status=RoleStatusGQL.INACTIVE → dto.status == RoleStatus.INACTIVE."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            status=RoleStatusGQL.INACTIVE,
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.status == RoleStatus.INACTIVE

    def test_multiple_fields_with_mixed_values(self) -> None:
        """Multiple fields with different values produce correct DTO."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            name="updated role",
            description=None,
            status=RoleStatusGQL.ACTIVE,
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.name == "updated role"
        assert dto.description is None
        assert dto.status == RoleStatus.ACTIVE

    def test_all_fields_unset_produces_all_defaults(self) -> None:
        """When all fields are UNSET, all DTO fields use their defaults."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # all fields omitted (UNSET by default)
        )

        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert dto.name is None
        assert dto.description is SENTINEL
        assert dto.status is None

    def test_id_is_on_gql_input_not_in_dto(self) -> None:
        """id is a GQL input field used for routing but not included in the DTO."""
        role_id = uuid.uuid4()
        role_input = UpdateRoleInput(id=role_id)

        assert role_input.id == role_id
        dto = role_input.to_pydantic()
        assert isinstance(dto, UpdateRoleInputDTO)
        assert not hasattr(dto, "id")
