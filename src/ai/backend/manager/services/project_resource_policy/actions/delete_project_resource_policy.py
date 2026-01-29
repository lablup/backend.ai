from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)


@dataclass
class DeleteProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Create return type.
    project_resource_policy: ProjectResourcePolicyData

    @override
    def entity_id(self) -> str | None:
        return self.project_resource_policy.name
