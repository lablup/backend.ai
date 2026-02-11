from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry_quota.actions.base import (
    ContainerRegistryQuotaAction,
)


@dataclass
class ReadQuotaAction(ContainerRegistryQuotaAction):
    scope_id: ProjectScope

    @override
    def entity_id(self) -> str | None:
        return str(self.scope_id.project_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ReadQuotaActionResult(BaseActionResult):
    scope_id: ProjectScope
    quota: int

    @override
    def entity_id(self) -> str | None:
        return str(self.scope_id.project_id)
