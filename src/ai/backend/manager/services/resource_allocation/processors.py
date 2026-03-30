"""Processors for resource allocation operations."""

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.resource_allocation.actions.check_preset_availability import (
    CheckPresetAvailabilityAction,
    CheckPresetAvailabilityActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_domain_usage import (
    GetDomainUsageAction,
    GetDomainUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_effective_allocation import (
    GetEffectiveAllocationAction,
    GetEffectiveAllocationActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_keypair_usage import (
    GetKeypairUsageAction,
    GetKeypairUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_project_usage import (
    GetProjectUsageAction,
    GetProjectUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_resource_group_usage import (
    GetResourceGroupUsageAction,
    GetResourceGroupUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.resolve_keypair_context import (
    ResolveKeypairContextAction,
    ResolveKeypairContextActionResult,
)
from ai.backend.manager.services.resource_allocation.service import ResourceAllocationService


class ResourceAllocationProcessors(AbstractProcessorPackage):
    resolve_keypair_context: ActionProcessor[
        ResolveKeypairContextAction, ResolveKeypairContextActionResult
    ]
    get_keypair_usage: ActionProcessor[GetKeypairUsageAction, GetKeypairUsageActionResult]
    get_project_usage: ActionProcessor[GetProjectUsageAction, GetProjectUsageActionResult]
    get_domain_usage: ActionProcessor[GetDomainUsageAction, GetDomainUsageActionResult]
    get_resource_group_usage: ActionProcessor[
        GetResourceGroupUsageAction, GetResourceGroupUsageActionResult
    ]
    get_effective_allocation: ActionProcessor[
        GetEffectiveAllocationAction, GetEffectiveAllocationActionResult
    ]
    check_preset_availability: ActionProcessor[
        CheckPresetAvailabilityAction, CheckPresetAvailabilityActionResult
    ]

    def __init__(
        self,
        service: ResourceAllocationService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.resolve_keypair_context = ActionProcessor(
            service.resolve_keypair_context, action_monitors
        )
        self.get_keypair_usage = ActionProcessor(service.get_keypair_usage, action_monitors)
        self.get_project_usage = ActionProcessor(service.get_project_usage, action_monitors)
        self.get_domain_usage = ActionProcessor(service.get_domain_usage, action_monitors)
        self.get_resource_group_usage = ActionProcessor(
            service.get_resource_group_usage, action_monitors
        )
        self.get_effective_allocation = ActionProcessor(
            service.get_effective_allocation, action_monitors
        )
        self.check_preset_availability = ActionProcessor(
            service.check_preset_availability, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveKeypairContextAction.spec(),
            GetKeypairUsageAction.spec(),
            GetProjectUsageAction.spec(),
            GetDomainUsageAction.spec(),
            GetResourceGroupUsageAction.spec(),
            GetEffectiveAllocationAction.spec(),
            CheckPresetAvailabilityAction.spec(),
        ]
