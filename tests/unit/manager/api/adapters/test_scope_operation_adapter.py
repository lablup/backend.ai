"""The scope operation catalog the adapter serves from the wiring."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import MagicMock

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE, DOMAIN_SCOPE_TYPE, DomainID
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
from ai.backend.manager.api.adapters.scope_operation.adapter import ScopeOperationAdapter
from ai.backend.manager.api.adapters.scope_operation.types import WiredScopeOperations
from ai.backend.manager.repositories.ops.repository import OpsRepository


@dataclass
class _ScopeResult(BaseScopeActionResult):
    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass
class _SearchInProject(BaseScopeAction):
    project_id: DomainID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.project_id),)

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
        return "search_in_project"


@dataclass
class _CreateAnywhere(BaseScopeAction):
    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return ()

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (GLOBAL_ENTITY_TYPE,)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_anywhere"


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


def _registry() -> ProcessorRegistry[Any]:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(MagicMock()),
        )
    )
    sessions = registry.group(GroupMeta(SESSION_ENTITY_TYPE))
    domains = registry.group(GroupMeta(DOMAIN_ENTITY_TYPE))
    sessions.scope(_SearchInProject, _run_scope)
    domains.scope(_CreateAnywhere, _run_scope)
    domains.single_entity(_GetOne, _run_single)
    return registry


def test_only_scope_shaped_wirings_are_listed() -> None:
    payload = ScopeOperationAdapter(WiredScopeOperations(_registry())).list_scope_operations()

    assert [item.action_name for item in payload.items] == ["create_anywhere", "search_in_project"]


def test_an_item_carries_the_declared_scope_types() -> None:
    payload = ScopeOperationAdapter(WiredScopeOperations(_registry())).list_scope_operations()
    item = next(item for item in payload.items if item.action_name == "search_in_project")

    assert item.entity_type == "session"
    assert item.operation == "search"
    assert item.scope_types == ["project", "user"]


def test_a_caller_named_scope_type_is_reported_as_global() -> None:
    payload = ScopeOperationAdapter(WiredScopeOperations(_registry())).list_scope_operations()
    item = next(item for item in payload.items if item.action_name == "create_anywhere")

    assert item.scope_types == ["global"]
