"""Processors for resource allocation operations."""

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
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


class ResourceAllocationProcessors:
    resolve_keypair_context: SingleEntityActionProcessor[
        ResolveKeypairContextAction, ResolveKeypairContextActionResult
    ]
    get_keypair_usage: SingleEntityActionProcessor[
        GetKeypairUsageAction, GetKeypairUsageActionResult
    ]
    get_project_usage: SingleEntityActionProcessor[
        GetProjectUsageAction, GetProjectUsageActionResult
    ]
    get_domain_usage: SingleEntityActionProcessor[GetDomainUsageAction, GetDomainUsageActionResult]
    get_resource_group_usage: GlobalActionProcessor[
        GetResourceGroupUsageAction, GetResourceGroupUsageActionResult
    ]
    get_effective_allocation: ScopeActionProcessor[
        GetEffectiveAllocationAction, GetEffectiveAllocationActionResult
    ]
    check_preset_availability: ScopeActionProcessor[
        CheckPresetAvailabilityAction, CheckPresetAvailabilityActionResult
    ]

    def __init__(
        self,
        user: ProcessorGroup[Any],
        project: ProcessorGroup[Any],
        domain: ProcessorGroup[Any],
        resource_group: ProcessorGroup[Any],
        session: ProcessorGroup[Any],
        resource_preset: ProcessorGroup[Any],
        service: ResourceAllocationService,
    ) -> None:
        self.resolve_keypair_context = user.single_entity(
            ResolveKeypairContextAction, service.resolve_keypair_context
        )
        self.get_keypair_usage = user.single_entity(
            GetKeypairUsageAction, service.get_keypair_usage
        )
        self.get_project_usage = project.single_entity(
            GetProjectUsageAction, service.get_project_usage
        )
        self.get_domain_usage = domain.single_entity(GetDomainUsageAction, service.get_domain_usage)
        self.get_resource_group_usage = resource_group.global_scope(
            GetResourceGroupUsageAction, service.get_resource_group_usage
        )
        self.get_effective_allocation = session.scope(
            GetEffectiveAllocationAction, service.get_effective_allocation
        )
        self.check_preset_availability = resource_preset.scope(
            CheckPresetAvailabilityAction, service.check_preset_availability
        )
