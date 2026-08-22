from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class DeleteRegistryQuotaAction(ContainerRegistryAction):
    scope_id: ProjectScope

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_registry_quota"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteRegistryQuotaActionResult:
    pass
