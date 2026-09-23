from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class CreateRegistryQuotaAction(ContainerRegistryAction):
    """Deprecated: authorized only by the API-layer gates of its callers.
    Add a scope-gated action and service method instead of extending this one."""

    scope_id: ProjectScope
    quota: int

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_registry_quota"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRegistryQuotaActionResult:
    pass
