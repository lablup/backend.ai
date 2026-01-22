from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.project_registry_quota.actions.create_project_registry_quota import (
    CreateProjectRegistryQuotaAction,
    CreateProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.delete_project_registry_quota import (
    DeleteProjectRegistryQuotaAction,
    DeleteProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.read_project_registry_quota import (
    ReadProjectRegistryQuotaAction,
    ReadProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.update_project_registry_quota import (
    UpdateProjectRegistryQuotaAction,
    UpdateProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.service import (
    ProjectRegistryQuotaService,
)


class ProjectRegistryQuotaProcessors(AbstractProcessorPackage):
    create_project_registry_quota: ActionProcessor[
        CreateProjectRegistryQuotaAction, CreateProjectRegistryQuotaActionResult
    ]
    read_project_registry_quota: ActionProcessor[
        ReadProjectRegistryQuotaAction, ReadProjectRegistryQuotaActionResult
    ]
    update_project_registry_quota: ActionProcessor[
        UpdateProjectRegistryQuotaAction, UpdateProjectRegistryQuotaActionResult
    ]
    delete_project_registry_quota: ActionProcessor[
        DeleteProjectRegistryQuotaAction, DeleteProjectRegistryQuotaActionResult
    ]

    def __init__(
        self, service: ProjectRegistryQuotaService, action_monitors: list[ActionMonitor]
    ) -> None:
        # Expose service for legacy gql access (gql_legacy/container_registry.py, group.py)
        self.service = service
        self.create_project_registry_quota = ActionProcessor(
            service.create_project_registry_quota, action_monitors
        )
        self.read_project_registry_quota = ActionProcessor(
            service.read_project_registry_quota, action_monitors
        )
        self.update_project_registry_quota = ActionProcessor(
            service.update_project_registry_quota, action_monitors
        )
        self.delete_project_registry_quota = ActionProcessor(
            service.delete_project_registry_quota, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateProjectRegistryQuotaAction.spec(),
            ReadProjectRegistryQuotaAction.spec(),
            UpdateProjectRegistryQuotaAction.spec(),
            DeleteProjectRegistryQuotaAction.spec(),
        ]
