from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.base import (
    ProjectResourcePolicyAction,
)
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class ProjectResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_network_count: OptionalState[int] = field(default_factory=OptionalState.nop)

    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_network_count.update_dict(to_update, "max_network_count")
        return to_update


@dataclass
class ModifyProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str
    modifier: ProjectResourcePolicyModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Add proper type
    project_resource_policy: ProjectResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
