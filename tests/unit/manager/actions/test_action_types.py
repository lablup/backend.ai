"""Tests for the action type system: ActionOperationType, EntityType, and enum enforcement."""

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import ErrorOperation
from ai.backend.manager.actions.types import ActionOperationType


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

    def test_to_permission_bit_maps_every_operation(self) -> None:
        assert ActionOperationType.GET.to_permission_bit() == Permission.READ
        assert ActionOperationType.SEARCH.to_permission_bit() == Permission.READ
        assert ActionOperationType.LOOKUP.to_permission_bit() == Permission.READ
        assert ActionOperationType.CREATE.to_permission_bit() == Permission.CREATE
        assert ActionOperationType.UPDATE.to_permission_bit() == Permission.UPDATE
        assert ActionOperationType.UPSERT.to_permission_bit() == Permission.CREATE
        assert ActionOperationType.DELETE.to_permission_bit() == Permission.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission_bit() == Permission.HARD_DELETE
        assert ActionOperationType.RESTORE.to_permission_bit() == Permission.SOFT_DELETE

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
