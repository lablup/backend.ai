from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.project_registry_quota.actions.base import (
    ProjectRegistryQuotaAction,
)


@dataclass
class UpdateProjectRegistryQuotaAction(ProjectRegistryQuotaAction):
    """Action to update a registry quota for a project."""

    project_id: UUID
    quota: int

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_project_registry_quota"


@dataclass
class UpdateProjectRegistryQuotaActionResult(BaseActionResult):
    """Result of updating a registry quota."""

    project_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)
