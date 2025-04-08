from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)


@dataclass
class CreateProjectResourcePolicyInputData:
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_vfolder_size: Optional[int]
    max_network_count: Optional[int]


@dataclass
class CreateProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str
    props: CreateProjectResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create"


@dataclass
class CreateProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create a return type.
    project_resource_policy: ProjectResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
