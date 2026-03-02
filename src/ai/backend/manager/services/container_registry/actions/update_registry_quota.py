from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class UpdateRegistryQuotaAction(ContainerRegistryAction):
    scope_id: ProjectScope
    quota: int

    @override
    def entity_id(self) -> str | None:
        return str(self.scope_id.project_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRegistryQuotaActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None
