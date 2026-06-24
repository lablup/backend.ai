"""Contract tests for action-target abstracts and their use in bulk actions.

Covers:

* :class:`ActionTarget` — RBAC element ref (universal across all action shapes).
* :class:`SearchableActionTarget` — RBAC ref + per-leaf :class:`SearchScope`.
* :class:`BaseBulkAction` parametrized on the target type so consumers see
  ``to_search_scope()`` without isinstance checks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.actions.action.types import ActionTarget, SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.repositories.base.types import ExistenceCheck, SearchScope


@dataclass(frozen=True)
class _StubSearchScope(SearchScope):
    column_value: str

    @override
    def to_condition(self) -> QueryCondition:
        value = self.column_value
        return lambda: sa.literal(value) == sa.literal(value)

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class _SearchableRefTarget(SearchableActionTarget):
    ref: RBACElementRef
    scope: _StubSearchScope

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return self.ref

    @override
    def to_search_scope(self) -> SearchScope:
        return self.scope


@dataclass
class _MockSearchableBulkAction(BaseBulkAction[SearchableActionTarget]):
    items: list[_SearchableRefTarget]

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


class TestSearchableActionTarget:
    def test_is_an_action_target(self) -> None:
        target = _SearchableRefTarget(
            ref=RBACElementRef(element_type=RBACElementType.VFOLDER, element_id="vf-1"),
            scope=_StubSearchScope(column_value="vf-1"),
        )

        assert isinstance(target, ActionTarget)

    def test_exposes_both_rbac_ref_and_search_scope(self) -> None:
        ref = RBACElementRef(element_type=RBACElementType.VFOLDER, element_id="vf-1")
        scope = _StubSearchScope(column_value="vf-1")
        target = _SearchableRefTarget(ref=ref, scope=scope)

        assert target.to_rbac_element_ref() == ref
        assert target.to_search_scope() is scope


class TestBulkActionWithSearchableTarget:
    def test_is_a_bulk_action(self) -> None:
        action = _MockSearchableBulkAction(items=[])

        assert isinstance(action, BaseBulkAction)

    def test_targets_yield_searchable_contract(self) -> None:
        ref_a = RBACElementRef(element_type=RBACElementType.VFOLDER, element_id="vf-a")
        ref_b = RBACElementRef(element_type=RBACElementType.USER, element_id="u-b")
        scope_a = _StubSearchScope(column_value="vf-a")
        scope_b = _StubSearchScope(column_value="u-b")
        action = _MockSearchableBulkAction(
            items=[
                _SearchableRefTarget(ref=ref_a, scope=scope_a),
                _SearchableRefTarget(ref=ref_b, scope=scope_b),
            ],
        )

        # Consumer can call both contracts on every target without isinstance.
        observed = [(t.to_rbac_element_ref(), t.to_search_scope()) for t in action.targets()]

        assert observed == [(ref_a, scope_a), (ref_b, scope_b)]
