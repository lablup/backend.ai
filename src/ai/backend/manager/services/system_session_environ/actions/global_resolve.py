from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData


@dataclass(frozen=True)
class GlobalResolveSystemSessionEnvironAction(BaseGlobalAction):
    """Read the rows a session in the domain and project receives, one per key."""

    domain_id: DomainID
    project_id: ProjectID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SystemSessionEnvironEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_resolve_system_session_environ"


@dataclass(frozen=True)
class GlobalResolveSystemSessionEnvironActionResult:
    effective_rows: list[SystemSessionEnvironData]
