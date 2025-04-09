from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)
from ai.backend.manager.types import Creator


@dataclass
class ProjectResourcePolicyCreator(Creator):
    name: str
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_vfolder_size: Optional[int]
    max_network_count: Optional[int]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            # "max_vfolder_size": self.max_vfolder_size, # deprecated fields
            "max_network_count": self.max_network_count,
        }


@dataclass
class CreateProjectResourcePolicyAction(ProjectResourcePolicyAction):
    creator: ProjectResourcePolicyCreator

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
