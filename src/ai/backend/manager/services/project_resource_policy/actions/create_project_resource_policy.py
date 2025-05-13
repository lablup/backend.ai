from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.types import ProjectResourcePolicyCreator


@dataclass
class CreateProjectResourcePolicyAction(ProjectResourcePolicyAction):
    creator: ProjectResourcePolicyCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create a return type.
    project_resource_policy: ProjectResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
