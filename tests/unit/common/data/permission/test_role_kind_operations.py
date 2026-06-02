"""Tests for the per-entity allowed-operation cached helpers."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.types import (
    OperationType,
    RBACElementType,
    admin_operations,
    member_operations,
    owner_operations,
)

_STANDARD_OPS: frozenset[OperationType] = frozenset({
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.HARD_DELETE,
})
_READ_ONLY_OPS: frozenset[OperationType] = frozenset({OperationType.READ})
_READ_AND_CREATE_OPS: frozenset[OperationType] = frozenset({
    OperationType.READ,
    OperationType.CREATE,
})
_VFOLDER_DATA_OWNER_OPS: frozenset[OperationType] = frozenset({
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.HARD_DELETE,
})

_MEMBER_CREATE_ENTITIES: frozenset[RBACElementType] = frozenset({
    RBACElementType.SESSION,
    RBACElementType.VFOLDER,
    RBACElementType.MODEL_DEPLOYMENT,
})

# vfolder:data and session:app_service are owner-only — admin and member
# operation sets are explicitly empty for these types.
_OWNER_ONLY_ENTITIES: frozenset[RBACElementType] = frozenset({
    RBACElementType.VFOLDER_DATA,
    RBACElementType.SESSION_APP_SERVICE,
})


class TestDefaultFallback:
    """Entity types not present in the override map fall back to the default set."""

    @pytest.mark.parametrize(
        "entity_type",
        [e for e in RBACElementType if e not in _OWNER_ONLY_ENTITIES],
    )
    def test_admin_fallback_is_standard_ops(self, entity_type: RBACElementType) -> None:
        assert admin_operations(entity_type) == _STANDARD_OPS

    @pytest.mark.parametrize(
        "entity_type",
        [e for e in RBACElementType if e not in _OWNER_ONLY_ENTITIES],
    )
    def test_owner_fallback_is_standard_ops(self, entity_type: RBACElementType) -> None:
        assert owner_operations(entity_type) == _STANDARD_OPS

    @pytest.mark.parametrize(
        "entity_type",
        [
            e
            for e in RBACElementType
            if e not in _MEMBER_CREATE_ENTITIES and e not in _OWNER_ONLY_ENTITIES
        ],
    )
    def test_member_fallback_is_read_only(self, entity_type: RBACElementType) -> None:
        assert member_operations(entity_type) == _READ_ONLY_OPS


class TestMemberCreateOverrides:
    """Members may CREATE sessions and vfolders in their scope."""

    @pytest.mark.parametrize("entity_type", sorted(_MEMBER_CREATE_ENTITIES, key=str))
    def test_member_can_create(self, entity_type: RBACElementType) -> None:
        assert member_operations(entity_type) == _READ_AND_CREATE_OPS


class TestOwnerOnlyOverrides:
    """vfolder:data and session:app_service are accessible only to the resource owner."""

    @pytest.mark.parametrize("entity_type", sorted(_OWNER_ONLY_ENTITIES, key=str))
    def test_admin_has_no_ops(self, entity_type: RBACElementType) -> None:
        assert admin_operations(entity_type) == frozenset()

    @pytest.mark.parametrize("entity_type", sorted(_OWNER_ONLY_ENTITIES, key=str))
    def test_member_has_no_ops(self, entity_type: RBACElementType) -> None:
        assert member_operations(entity_type) == frozenset()

    def test_vfolder_data_owner_has_crud_without_soft_delete(self) -> None:
        # vfolder data has no two-stage delete, so soft-delete is intentionally omitted.
        assert owner_operations(RBACElementType.VFOLDER_DATA) == _VFOLDER_DATA_OWNER_OPS
        assert OperationType.SOFT_DELETE not in owner_operations(RBACElementType.VFOLDER_DATA)

    def test_session_app_service_owner_is_read_only(self) -> None:
        assert owner_operations(RBACElementType.SESSION_APP_SERVICE) == _READ_ONLY_OPS


class TestPurity:
    """The helpers are pure functions of their argument."""

    def test_admin_is_pure(self) -> None:
        first = admin_operations(RBACElementType.SESSION)
        admin_operations(RBACElementType.VFOLDER)
        admin_operations(RBACElementType.AGENT)
        assert admin_operations(RBACElementType.SESSION) == first

    def test_member_is_pure(self) -> None:
        first = member_operations(RBACElementType.SESSION)
        member_operations(RBACElementType.VFOLDER)
        assert member_operations(RBACElementType.SESSION) == first
