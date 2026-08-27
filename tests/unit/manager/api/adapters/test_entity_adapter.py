"""The scope types the entity type listing carries, read off the wiring."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import MagicMock

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import (
    GLOBAL_ENTITY_TYPE,
    EntityIdentifier,
    EntityType,
    ScopeRef,
)
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.api.adapters.entity.adapter import EntityAdapter
from ai.backend.manager.api.adapters.entity.types import WiredEntityTypes
from ai.backend.manager.repositories.ops.repository import OpsRepository


@dataclass
class _ScopeResult(BaseScopeActionResult):
    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass
class _ScopeAction(BaseScopeAction):
    """Declares a pair, as an action branching on its input does."""

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return ()

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE, USER_ENTITY_TYPE)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_in_scope"


@dataclass
class _OtherScopeAction(_ScopeAction):
    """A second operation on the same entity, overlapping the first by one type."""

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (DOMAIN_ENTITY_TYPE, USER_ENTITY_TYPE)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_in_other_scope"


@dataclass
class _DanglingScopeAction(_ScopeAction):
    """A read the wiring gives no entity type, as a dangling field read is."""

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (DOMAIN_ENTITY_TYPE,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_dangling"


@dataclass
class _GetOne(BaseSingleEntityAction):
    domain_id: DomainID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_one"


async def _run_scope(action: Any) -> _ScopeResult:
    return _ScopeResult()


async def _run_single(action: Any) -> Any:
    return MagicMock()


def _wired(*, several: bool = False) -> WiredEntityTypes:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(MagicMock()),
        )
    )
    sessions = registry.group(GroupMeta(SESSION_ENTITY_TYPE))
    sessions.scope(_ScopeAction, _run_scope)
    if several:
        sessions.scope(_OtherScopeAction, _run_scope)
    registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)).single_entity(_GetOne, _run_single)
    registry.group(GroupMeta(GLOBAL_ENTITY_TYPE)).scope(_DanglingScopeAction, _run_scope)
    return WiredEntityTypes(registry)


def _items() -> dict[str, list[str]]:
    payload = EntityAdapter(_wired()).list_entity_types()
    return {item.name: item.scope_types for item in payload.items}


def test_an_entity_type_carries_what_its_scope_operations_declare() -> None:
    assert _items()["session"] == ["project", "user"]


def test_an_entity_type_nothing_scopes_carries_no_scope_type() -> None:
    assert _items()["domain"] == []


def test_a_scope_operation_the_wiring_gives_no_entity_type_is_left_out() -> None:
    """A dangling field read is wired under `global`, which names no entity.

    Its declaration reaches `mgr ops list` and stops there: there is no entity type in
    this listing for it to belong to.
    """
    items = _items()

    assert "global" not in items
    assert "domain" in items
    assert items["domain"] == []


def test_the_declarations_of_several_operations_are_merged_in_name_order() -> None:
    payload = EntityAdapter(_wired(several=True)).list_entity_types()
    session = next(item for item in payload.items if item.name == "session")

    assert session.scope_types == ["domain", "project", "user"]
