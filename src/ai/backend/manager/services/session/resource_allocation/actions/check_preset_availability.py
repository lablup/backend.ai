from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.resource_allocation.types import PresetAvailabilityData


@dataclass(frozen=True)
class CheckPresetAvailabilityAction(BaseScopeAction):
    """Read which presets a caller could start in a project right now."""

    access_key: AccessKey
    user_id: UserID
    project_id: ProjectID
    domain_name: str
    resource_policy: Mapping[str, Any]
    rg_name: str
    group_resource_visibility: bool
    hide_agents: bool
    is_admin: bool
    resource_group: str | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_PRESET_ENTITY_TYPE

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
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "check_preset_availability"


@dataclass(frozen=True)
class CheckPresetAvailabilityActionResult(BaseScopeActionResult):
    presets: list[PresetAvailabilityData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
