"""Unit tests for UpdateRoleInput.to_updater()."""

from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.manager.api.gql.rbac.types.role import RoleStatusGQL, UpdateRoleInput
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import _TriStateEnum


class TestUpdateRoleInputToUpdater:
    """Tests for UpdateRoleInput.to_updater() method."""

    def test_description_with_none_creates_nullify_tristate(self) -> None:
        """UpdateRoleInput with description=None → TriState.nullify() in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            description=None,
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.description._state == _TriStateEnum.NULLIFY

    def test_description_with_unset_creates_nop_tristate(self) -> None:
        """UpdateRoleInput with description=UNSET → TriState.nop() in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # description is omitted (UNSET by default)
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.description._state == _TriStateEnum.NOP

    def test_description_with_string_creates_update_tristate(self) -> None:
        """UpdateRoleInput with description="text" → TriState.update("text") in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            description="some text",
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.description._state == _TriStateEnum.UPDATE
        assert spec.description.value() == "some text"

    def test_name_with_unset_creates_nop_optionalstate(self) -> None:
        """UpdateRoleInput with name=UNSET → OptionalState.nop() in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # name is omitted (UNSET by default)
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.name._state == _TriStateEnum.NOP

    def test_name_with_string_creates_update_optionalstate(self) -> None:
        """UpdateRoleInput with name="new name" → OptionalState.update("new name") in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            name="new name",
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.name._state == _TriStateEnum.UPDATE
        assert spec.name.value() == "new name"

    def test_status_with_unset_creates_nop_optionalstate(self) -> None:
        """UpdateRoleInput with status=UNSET → OptionalState.nop() in updater spec."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # status is omitted (UNSET by default)
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.status._state == _TriStateEnum.NOP

    def test_status_with_active_creates_update_optionalstate(self) -> None:
        """UpdateRoleInput with status=RoleStatusGQL.ACTIVE → OptionalState.update(RoleStatus.ACTIVE)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            status=RoleStatusGQL.ACTIVE,
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.status._state == _TriStateEnum.UPDATE
        assert spec.status.value() == RoleStatus.ACTIVE

    def test_status_with_inactive_creates_update_optionalstate(self) -> None:
        """UpdateRoleInput with status=RoleStatusGQL.INACTIVE → OptionalState.update(RoleStatus.INACTIVE)."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            status=RoleStatusGQL.INACTIVE,
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.status._state == _TriStateEnum.UPDATE
        assert spec.status.value() == RoleStatus.INACTIVE

    def test_multiple_fields_with_mixed_states(self) -> None:
        """Test multiple fields with different states."""
        role_id = uuid.uuid4()
        role_input = UpdateRoleInput(
            id=role_id,
            name="updated role",
            description=None,
            status=RoleStatusGQL.ACTIVE,
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert updater.pk_value == role_id
        assert spec.name._state == _TriStateEnum.UPDATE
        assert spec.name.value() == "updated role"
        assert spec.description._state == _TriStateEnum.NULLIFY
        assert spec.status._state == _TriStateEnum.UPDATE
        assert spec.status.value() == RoleStatus.ACTIVE

    def test_all_fields_unset_creates_all_nop(self) -> None:
        """When all fields are UNSET, all spec fields should be nop."""
        role_input = UpdateRoleInput(
            id=uuid.uuid4(),
            # all fields omitted (UNSET by default)
        )

        updater = role_input.to_updater()
        spec = updater.spec
        assert isinstance(spec, RoleUpdaterSpec)

        assert spec.name._state == _TriStateEnum.NOP
        assert spec.description._state == _TriStateEnum.NOP
        assert spec.status._state == _TriStateEnum.NOP

    def test_updater_pk_value_matches_input_id(self) -> None:
        """Updater.pk_value should match the input id."""
        role_id = uuid.uuid4()
        role_input = UpdateRoleInput(id=role_id)

        updater = role_input.to_updater()

        assert updater.pk_value == role_id
