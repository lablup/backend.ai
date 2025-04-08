from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
)
from ai.backend.manager.services.project_resource_policy.base import ProjectResourcePolicyAction
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyProjectResourcePolicyInputData:
    max_vfolder_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_count")
    )
    max_quota_scope_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_quota_scope_size")
    )
    max_vfolder_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_size")
    )
    max_network_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_network_count")
    )

    def set_attr(self, row: Any) -> None:
        self.max_vfolder_count.set_attr(row)
        self.max_quota_scope_size.set_attr(row)
        self.max_vfolder_size.set_attr(row)
        self.max_network_count.set_attr(row)


@dataclass
class ModifyProjectResourcePolicyAction(ProjectResourcePolicyAction):
    name: str
    props: ModifyProjectResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify_project_resource_policy"


@dataclass
class ModifyProjectResourcePolicyActionResult(BaseActionResult):
    # TODO: Add proper type
    project_resource_policy: ProjectResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.project_resource_policy.name
