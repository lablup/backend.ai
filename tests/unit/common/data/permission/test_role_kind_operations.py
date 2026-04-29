"""Tests for the per-entity allowed-operation cached helpers."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission import types as perm_types
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


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    """Reset the cache between tests so override mutations take effect."""
    admin_operations.cache_clear()
    owner_operations.cache_clear()
    member_operations.cache_clear()


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


class TestOverrideMap:
    """When the override map carries an entry, the helper returns it."""

    def test_admin_override_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        override = frozenset({OperationType.READ})
        monkeypatch.setitem(
            perm_types._ADMIN_OPS_OVERRIDES,
            RBACElementType.SESSION,
            override,
        )
        admin_operations.cache_clear()
        assert admin_operations(RBACElementType.SESSION) == override
        assert admin_operations(RBACElementType.VFOLDER) == _STANDARD_OPS  # untouched

    def test_owner_override_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        override = frozenset({OperationType.READ, OperationType.UPDATE})
        monkeypatch.setitem(
            perm_types._OWNER_OPS_OVERRIDES,
            RBACElementType.MODEL_DEPLOYMENT,
            override,
        )
        owner_operations.cache_clear()
        assert owner_operations(RBACElementType.MODEL_DEPLOYMENT) == override

    def test_member_override_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        override: frozenset[OperationType] = frozenset()
        monkeypatch.setitem(
            perm_types._MEMBER_OPS_OVERRIDES,
            RBACElementType.AGENT,
            override,
        )
        member_operations.cache_clear()
        assert member_operations(RBACElementType.AGENT) == override


class TestCacheStability:
    """Repeated calls return the same frozenset instance (cache hits)."""

    def test_admin_returns_same_object(self) -> None:
        assert admin_operations(RBACElementType.SESSION) is admin_operations(
            RBACElementType.SESSION
        )

    def test_owner_returns_same_object(self) -> None:
        assert owner_operations(RBACElementType.SESSION) is owner_operations(
            RBACElementType.SESSION
        )

    def test_member_returns_same_object(self) -> None:
        assert member_operations(RBACElementType.SESSION) is member_operations(
            RBACElementType.SESSION
        )


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
