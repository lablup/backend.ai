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

_MEMBER_CREATE_ENTITIES: frozenset[RBACElementType] = frozenset({
    RBACElementType.SESSION,
    RBACElementType.VFOLDER,
    RBACElementType.MODEL_DEPLOYMENT,
})


class TestDefaultFallback:
    """Entity types not present in the override map fall back to the default set."""

    @pytest.mark.parametrize("entity_type", list(RBACElementType))
    def test_admin_fallback_is_standard_ops(self, entity_type: RBACElementType) -> None:
        assert admin_operations(entity_type) == _STANDARD_OPS

    @pytest.mark.parametrize("entity_type", list(RBACElementType))
    def test_owner_fallback_is_standard_ops(self, entity_type: RBACElementType) -> None:
        assert owner_operations(entity_type) == _STANDARD_OPS

    @pytest.mark.parametrize(
        "entity_type",
        [e for e in RBACElementType if e not in _MEMBER_CREATE_ENTITIES],
    )
    def test_member_fallback_is_read_only(self, entity_type: RBACElementType) -> None:
        assert member_operations(entity_type) == _READ_ONLY_OPS


class TestMemberCreateOverrides:
    """Members may CREATE sessions and vfolders in their scope."""

    @pytest.mark.parametrize("entity_type", sorted(_MEMBER_CREATE_ENTITIES, key=str))
    def test_member_can_create(self, entity_type: RBACElementType) -> None:
        assert member_operations(entity_type) == _READ_AND_CREATE_OPS


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
