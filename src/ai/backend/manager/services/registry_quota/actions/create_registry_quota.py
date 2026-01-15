from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.registry_quota.actions.base import RegistryQuotaAction


@dataclass
class CreateRegistryQuotaAction(RegistryQuotaAction):
    """Action to create a registry quota for a project."""

    project_id: UUID
    quota: int

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_registry_quota"


@dataclass
class CreateRegistryQuotaActionResult(BaseActionResult):
    """Result of creating a registry quota."""

    project_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)
