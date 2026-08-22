from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class UpdateRegistryQuotaAction(ContainerRegistryAction):
    scope_id: ProjectScope
    quota: int

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_registry_quota"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRegistryQuotaActionResult:
    pass
