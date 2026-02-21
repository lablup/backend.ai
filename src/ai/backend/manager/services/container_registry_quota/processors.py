from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.container_registry_quota.actions.create_quota import (
    CreateQuotaAction,
    CreateQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.delete_quota import (
    DeleteQuotaAction,
    DeleteQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.read_quota import (
    ReadQuotaAction,
    ReadQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.update_quota import (
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.service import (
    ContainerRegistryQuotaService,
)


class ContainerRegistryQuotaProcessors(AbstractProcessorPackage):
    create_quota: ActionProcessor[CreateQuotaAction, CreateQuotaActionResult]
    update_quota: ActionProcessor[UpdateQuotaAction, UpdateQuotaActionResult]
    delete_quota: ActionProcessor[DeleteQuotaAction, DeleteQuotaActionResult]
    read_quota: ActionProcessor[ReadQuotaAction, ReadQuotaActionResult]

    def __init__(
        self, service: ContainerRegistryQuotaService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_quota = ActionProcessor(service.create_quota, action_monitors)
        self.update_quota = ActionProcessor(service.update_quota, action_monitors)
        self.delete_quota = ActionProcessor(service.delete_quota, action_monitors)
        self.read_quota = ActionProcessor(service.read_quota, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateQuotaAction.spec(),
            UpdateQuotaAction.spec(),
            DeleteQuotaAction.spec(),
            ReadQuotaAction.spec(),
        ]
