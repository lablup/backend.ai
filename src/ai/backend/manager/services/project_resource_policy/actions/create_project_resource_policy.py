from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
)
from ai.backend.manager.services.project_resource_policy.base import ProjectResourcePolicyAction


@dataclass
class CreateProjectResourcePolicyInput:
    max_vfolder_count: Optional[int] = None
    max_quota_scope_size: Optional[int] = None
    max_vfolder_size: Optional[int] = None
    max_network_count: Optional[int] = None


@dataclass
class CreateProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str
    props: CreateProjectResourcePolicyInput

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_project_resource_policy"


@dataclass
class CreateProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create a return type.
    project_resource_policy: ProjectResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
