"""Tests for the action type system: ActionOperationType, EntityType, and enum enforcement."""

import pytest

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import OperationType, Permission
from ai.backend.common.exception import ErrorOperation
from ai.backend.manager.actions.action.base import BaseAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
)

# Import representative concrete action classes across different entity types
# and operation types to verify enum usage at runtime.
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.actions.role.revoke import RevokeRoleAction

# Legacy-family actions only. The v2 families answer with
# ``ai.backend.common.data.entity.types.EntityType``, a distinct NewType, so mixing
# them in would conflate two type systems rather than test either one.
_REPRESENTATIVE_ACTION_CLASSES: list[type[BaseAction]] = [
    AssignRoleAction,
    GetRoleDetailAction,
    ReplaceRolePermissionsAction,
    RevokeRoleAction,
    SearchRolesAction,
]


class TestActionOperationType:
    def test_has_exactly_nine_values(self) -> None:
        values = list(ActionOperationType)
        assert len(values) == 9
        expected = {
            "get",
            "search",
            "create",
            "update",
            "upsert",
            "delete",
            "purge",
            "restore",
            "lookup",
        }
        assert {v.value for v in values} == expected

    @pytest.mark.parametrize(
        ("operation", "expected"),
        [
            (ActionOperationType.GET, ErrorOperation.READ),
            (ActionOperationType.SEARCH, ErrorOperation.SEARCH),
            (ActionOperationType.LOOKUP, ErrorOperation.READ),
            (ActionOperationType.CREATE, ErrorOperation.CREATE),
            (ActionOperationType.UPSERT, ErrorOperation.UPSERT),
            (ActionOperationType.UPDATE, ErrorOperation.UPDATE),
            (ActionOperationType.RESTORE, ErrorOperation.RESTORE),
            (ActionOperationType.DELETE, ErrorOperation.SOFT_DELETE),
            (ActionOperationType.PURGE, ErrorOperation.HARD_DELETE),
        ],
    )
    def test_to_error_operation_mapping(
        self, operation: ActionOperationType, expected: ErrorOperation
    ) -> None:
        assert operation.to_error_operation() is expected

    def test_to_permission_operation_mapping(self) -> None:
        assert ActionOperationType.GET.to_permission_operation() == OperationType.READ
        assert ActionOperationType.SEARCH.to_permission_operation() == OperationType.READ
        assert ActionOperationType.LOOKUP.to_permission_operation() == OperationType.READ
        assert ActionOperationType.CREATE.to_permission_operation() == OperationType.CREATE
        assert ActionOperationType.UPDATE.to_permission_operation() == OperationType.UPDATE
        assert ActionOperationType.UPSERT.to_permission_operation() == OperationType.CREATE
        assert ActionOperationType.DELETE.to_permission_operation() == OperationType.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission_operation() == OperationType.HARD_DELETE
        assert ActionOperationType.RESTORE.to_permission_operation() == OperationType.SOFT_DELETE

    def test_to_permission_mapping(self) -> None:
        assert ActionOperationType.GET.to_permission() == Permission.READ
        assert ActionOperationType.SEARCH.to_permission() == Permission.READ
        assert ActionOperationType.LOOKUP.to_permission() == Permission.READ
        assert ActionOperationType.CREATE.to_permission() == Permission.CREATE
        assert ActionOperationType.UPDATE.to_permission() == Permission.UPDATE
        assert ActionOperationType.DELETE.to_permission() == Permission.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission() == Permission.HARD_DELETE
        assert ActionOperationType.RESTORE.to_permission() == Permission.SOFT_DELETE

    def test_upsert_requires_both_create_and_update(self) -> None:
        """An upsert may insert or overwrite, so neither bit alone is sufficient."""
        required = ActionOperationType.UPSERT.to_permission()
        assert required == Permission.CREATE | Permission.UPDATE
        assert not Permission.CREATE.covers(required)
        assert not Permission.UPDATE.covers(required)
        assert (Permission.CREATE | Permission.UPDATE).covers(required)

    def test_to_permission_covers_every_operation(self) -> None:
        for op in ActionOperationType:
            assert op.to_permission() != Permission.NONE

    def test_all_values_are_unique(self) -> None:
        values = [v.value for v in ActionOperationType]
        assert len(values) == len(set(values))

    def test_is_str_subclass(self) -> None:
        for v in ActionOperationType:
            assert isinstance(v, str)


class TestAllActionClassesUseEnums:
    """Verify that representative concrete action classes return proper enum types.

    These tests cover the operations concrete legacy actions declare today (GET,
    SEARCH, CREATE, UPDATE, DELETE) via representative concrete action classes.
    """

    def test_entity_type_returns_enum(self) -> None:
        for cls in _REPRESENTATIVE_ACTION_CLASSES:
            result = cls.entity_type()
            assert isinstance(result, EntityType), (
                f"{cls.__name__}.entity_type() returned {type(result).__name__} "
                f"({result!r}), expected EntityType"
            )

    def test_operation_type_returns_enum(self) -> None:
        for cls in _REPRESENTATIVE_ACTION_CLASSES:
            result = cls.operation_type()
            assert isinstance(result, ActionOperationType), (
                f"{cls.__name__}.operation_type() returned {type(result).__name__} "
                f"({result!r}), expected ActionOperationType"
            )

    def test_covers_all_operation_types(self) -> None:
        """Ensure the representative classes cover every declarable operation.

        ``UPSERT`` is excluded: the upsert actions declare ``CREATE`` today, so
        nothing can stand for it. ``LOOKUP``, ``PURGE`` and ``RESTORE`` are excluded
        because no legacy action declares them, and every class here is a legacy one.
        """
        expected = set(ActionOperationType) - {
            ActionOperationType.UPSERT,
            ActionOperationType.LOOKUP,
            ActionOperationType.PURGE,
            ActionOperationType.RESTORE,
        }
        covered = {cls.operation_type() for cls in _REPRESENTATIVE_ACTION_CLASSES}
        assert covered == expected, (
            f"Not all ActionOperationType values are covered. Missing: {expected - covered}"
        )
