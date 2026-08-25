from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.resource_slot.types import ResourceOccupancy


@dataclass(frozen=True)
class GetProjectResourceOverviewAction(BaseScopeAction):
    """Read what the sessions inside a project occupy."""

    project_id: ProjectID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_project_resource_overview"


@dataclass(frozen=True)
class GetProjectResourceOverviewResult(BaseScopeActionResult):
    item: ResourceOccupancy

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
