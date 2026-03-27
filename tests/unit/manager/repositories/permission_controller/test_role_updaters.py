"""Unit tests for RoleUpdaterSpec."""

from __future__ import annotations

from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


class TestRoleUpdaterSpecBuildValues:
    """Tests for RoleUpdaterSpec.build_values() method."""

    def test_build_values_with_all_nop_returns_empty_dict(self) -> None:
        """When all fields are nop, build_values should return empty dict."""
        spec = RoleUpdaterSpec()

        result = spec.build_values()

        assert result == {}

    def test_build_values_with_description_nullify(self) -> None:
        """When description is nullify, build_values should include description: None."""
        spec = RoleUpdaterSpec(
            description=TriState.nullify(),
        )

        result = spec.build_values()

        assert result == {"description": None}

    def test_build_values_with_description_nop(self) -> None:
        """When description is nop, build_values should not include description key."""
        spec = RoleUpdaterSpec(
            description=TriState.nop(),
        )

        result = spec.build_values()

        assert "description" not in result

    def test_build_values_with_description_update(self) -> None:
        """When description is update, build_values should include the description value."""
        spec = RoleUpdaterSpec(
            description=TriState.update("Updated description"),
        )

        result = spec.build_values()

        assert result == {"description": "Updated description"}

    def test_build_values_with_name_update(self) -> None:
        """Test name field is included when set."""
        spec = RoleUpdaterSpec(
            name=OptionalState.update("new_role_name"),
        )

        result = spec.build_values()

        assert result == {"name": "new_role_name"}

    def test_build_values_with_status_update(self) -> None:
        """Test status field is included when set."""
        spec = RoleUpdaterSpec(
            status=OptionalState.update(RoleStatus.ACTIVE),
        )

        result = spec.build_values()

        assert result == {"status": RoleStatus.ACTIVE}

    def test_build_values_with_source_update(self) -> None:
        """Test source field is included when set."""
        spec = RoleUpdaterSpec(
            source=OptionalState.update(RoleSource.CUSTOM),
        )

        result = spec.build_values()

        assert result == {"source": RoleSource.CUSTOM}

    def test_build_values_with_multiple_fields(self) -> None:
        """Test multiple fields are correctly included."""
        spec = RoleUpdaterSpec(
            name=OptionalState.update("updated_role"),
            source=OptionalState.update(RoleSource.CUSTOM),
            status=OptionalState.update(RoleStatus.INACTIVE),
            description=TriState.update("Updated role description"),
        )

        result = spec.build_values()

        assert result == {
            "name": "updated_role",
            "source": RoleSource.CUSTOM,
            "status": RoleStatus.INACTIVE,
            "description": "Updated role description",
        }

    def test_build_values_with_mixed_states(self) -> None:
        """Test with a mix of nop, update, and nullify states."""
        spec = RoleUpdaterSpec(
            name=OptionalState.update("role_name"),
            source=OptionalState.nop(),  # Should not be included
            status=OptionalState.update(RoleStatus.ACTIVE),
            description=TriState.nullify(),  # Should be None
        )

        result = spec.build_values()

        assert result == {
            "name": "role_name",
            "status": RoleStatus.ACTIVE,
            "description": None,
        }


class TestRoleUpdaterSpecRowClass:
    """Tests for RoleUpdaterSpec.row_class property."""

    def test_row_class_returns_role_row(self) -> None:
        """row_class should return RoleRow."""
        spec = RoleUpdaterSpec()

        assert spec.row_class is RoleRow
