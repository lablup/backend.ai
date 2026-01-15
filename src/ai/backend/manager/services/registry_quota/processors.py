from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.registry_quota.actions.create_registry_quota import (
    CreateRegistryQuotaAction,
    CreateRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.delete_registry_quota import (
    DeleteRegistryQuotaAction,
    DeleteRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
    ReadRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
    UpdateRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.service import RegistryQuotaService


class RegistryQuotaProcessors(AbstractProcessorPackage):
    create_registry_quota: ActionProcessor[
        CreateRegistryQuotaAction, CreateRegistryQuotaActionResult
    ]
    read_registry_quota: ActionProcessor[ReadRegistryQuotaAction, ReadRegistryQuotaActionResult]
    update_registry_quota: ActionProcessor[
        UpdateRegistryQuotaAction, UpdateRegistryQuotaActionResult
    ]
    delete_registry_quota: ActionProcessor[
        DeleteRegistryQuotaAction, DeleteRegistryQuotaActionResult
    ]

    def __init__(self, service: RegistryQuotaService, action_monitors: list[ActionMonitor]) -> None:
        # Expose service for legacy gql access (gql_legacy/container_registry.py)
        self._service = service
        self.create_registry_quota = ActionProcessor(service.create_registry_quota, action_monitors)
        self.read_registry_quota = ActionProcessor(service.read_registry_quota, action_monitors)
        self.update_registry_quota = ActionProcessor(service.update_registry_quota, action_monitors)
        self.delete_registry_quota = ActionProcessor(service.delete_registry_quota, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRegistryQuotaAction.spec(),
            ReadRegistryQuotaAction.spec(),
            UpdateRegistryQuotaAction.spec(),
            DeleteRegistryQuotaAction.spec(),
        ]
