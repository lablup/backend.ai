from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.resource_allocation.types import EffectiveAllocationData


@dataclass(frozen=True)
class GetEffectiveAllocationAction(BaseScopeAction):
    """Read the allocation a caller effectively has in a project right now."""

    access_key: AccessKey
    user_id: UserID
    project_id: ProjectID
    domain_name: str
    resource_policy: Mapping[str, Any]
    rg_name: str
    group_resource_visibility: bool
    hide_agents: bool
    is_admin: bool

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project_id,)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_effective_allocation"


@dataclass(frozen=True)
class GetEffectiveAllocationActionResult(BaseScopeActionResult):
    allocation: EffectiveAllocationData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
