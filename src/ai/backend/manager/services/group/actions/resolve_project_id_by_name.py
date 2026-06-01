"""Action for resolving a project's UUID by its domain-scoped name."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.project import ProjectID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class ResolveProjectIdByNameAction(GroupAction):
    """Resolve an active project's UUID by its `(domain_name, project_name)` pair."""

    domain_name: str
    project_name: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveProjectIdByNameActionResult(BaseActionResult):
    """Result carrying the resolved project UUID."""

    project_id: ProjectID | None

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id) if self.project_id is not None else None
