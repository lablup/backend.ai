from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
)
from ai.backend.manager.services.project_resource_policy.base import ProjectResourcePolicyAction


@dataclass
class DeleteProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "delete_project_resource_policy"


@dataclass
class DeleteProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create return type.
    project_resource_policy: ProjectResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
