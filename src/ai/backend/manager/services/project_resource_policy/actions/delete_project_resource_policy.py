from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)


@dataclass
class DeleteProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "delete"


@dataclass
class DeleteProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create return type.
    project_resource_policy: ProjectResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
