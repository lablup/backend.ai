from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
    CreateProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
    DeleteProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ModifyProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService


class ProjectResourcePolicyProcessors(AbstractProcessorPackage):
    create_project_resource_policy: ActionProcessor[
        CreateProjectResourcePolicyAction, CreateProjectResourcePolicyActionResult
    ]
    modify_project_resource_policy: ActionProcessor[
        ModifyProjectResourcePolicyAction, ModifyProjectResourcePolicyActionResult
    ]
    delete_project_resource_policy: ActionProcessor[
        DeleteProjectResourcePolicyAction, DeleteProjectResourcePolicyActionResult
    ]

    def __init__(
        self, service: ProjectResourcePolicyService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_project_resource_policy = ActionProcessor(
            service.create_project_resource_policy, action_monitors
        )
        self.modify_project_resource_policy = ActionProcessor(
            service.modify_project_resource_policy, action_monitors
        )
        self.delete_project_resource_policy = ActionProcessor(
            service.delete_project_resource_policy, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateProjectResourcePolicyAction.spec(),
            ModifyProjectResourcePolicyAction.spec(),
            DeleteProjectResourcePolicyAction.spec(),
        ]
