"""Factory functions for creating scheduler components and coordinator handlers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from ai.backend.manager.sokovan.scheduler.handlers import (
    CheckPreconditionLifecycleHandler,
    DeprioritizeSessionsLifecycleHandler,
    DetectTerminationPromotionHandler,
    PromoteToPreparedPromotionHandler,
    PromoteToRunningPromotionHandler,
    PromoteToTerminatedPromotionHandler,
    ScheduleSessionsLifecycleHandler,
    SessionLifecycleHandler,
    SessionPromotionHandler,
    StartSessionsLifecycleHandler,
    SweepSessionsLifecycleHandler,
    TerminateSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.handlers.kernel import (
    KernelLifecycleHandler,
    SweepStaleKernelsKernelHandler,
)
from ai.backend.manager.sokovan.scheduler.launcher.launcher import (
    SessionLauncher,
    SessionLauncherArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.allocators.repository_allocator import (
    RepositoryAllocator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
    SessionProvisionerArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.validators.concurrency import (
    ConcurrencyValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.dependencies import (
    DependenciesValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.domain_resource_limit import (
    DomainResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.group_resource_limit import (
    GroupResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.keypair_resource_limit import (
    KeypairResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.pending_session_count_limit import (
    PendingSessionCountLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.pending_session_resource_limit import (
    PendingSessionResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.reserved_batch import (
    ReservedBatchSessionValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.user_resource_limit import (
    UserResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.validator import (
    SchedulingValidator,
)
from ai.backend.manager.sokovan.scheduler.scheduler import (
    SchedulerComponents,
    create_scheduler_components,
)
from ai.backend.manager.sokovan.scheduler.terminator.terminator import (
    SessionTerminator,
    SessionTerminatorArgs,
)


def create_default_scheduler_components(
    repository: SchedulerRepository,
    deployment_repository: DeploymentRepository,
    config_provider: ManagerConfigProvider,
    agent_client_pool: AgentClientPool,
    network_plugin_ctx: NetworkPluginContext,
    event_producer: EventProducer,
    valkey_schedule: ValkeyScheduleClient,
) -> SchedulerComponents:
    """
    Create scheduler components with default configuration.

    Args:
        repository: The repository for accessing system data
        deployment_repository: The deployment repository
        config_provider: The manager configuration provider
        agent_client_pool: Pool for managing agent clients
        network_plugin_ctx: Network plugin context for network management
        event_producer: Event producer for publishing events
        valkey_schedule: Valkey client for scheduling operations

    Returns:
        A configured SchedulerComponents instance
    """
    # Create provisioner components
    sequencer = FIFOSequencer()
    validator = SchedulingValidator([
        ConcurrencyValidator(),
        DependenciesValidator(),
        DomainResourceLimitValidator(),
        GroupResourceLimitValidator(),
        KeypairResourceLimitValidator(),
        PendingSessionCountLimitValidator(),
        PendingSessionResourceLimitValidator(),
        ReservedBatchSessionValidator(),
        UserResourceLimitValidator(),
    ])
    resource_priority = config_provider.config.manager.agent_selection_resource_priority
    agent_selector = AgentSelector(ConcentratedAgentSelector(resource_priority))
    allocator = RepositoryAllocator(repository)

    # Create provisioner
    provisioner = SessionProvisioner(
        SessionProvisionerArgs(
            validator=validator,
            default_sequencer=sequencer,
            default_agent_selector=agent_selector,
            allocator=allocator,
            repository=repository,
            config_provider=config_provider,
            valkey_schedule=valkey_schedule,
        )
    )

    # Create launcher
    launcher = SessionLauncher(
        SessionLauncherArgs(
            repository=repository,
            agent_client_pool=agent_client_pool,
            network_plugin_ctx=network_plugin_ctx,
            config_provider=config_provider,
            valkey_schedule=valkey_schedule,
        )
    )

    # Create terminator
    terminator = SessionTerminator(
        SessionTerminatorArgs(
            repository=repository,
            agent_client_pool=agent_client_pool,
            valkey_schedule=valkey_schedule,
        )
    )

    return create_scheduler_components(
        provisioner=provisioner,
        launcher=launcher,
        terminator=terminator,
        repository=repository,
        deployment_repository=deployment_repository,
        config_provider=config_provider,
        agent_client_pool=agent_client_pool,
        event_producer=event_producer,
    )


# =============================================================================
# Coordinator Handlers
# =============================================================================


@dataclass
class CoordinatorHandlers:
    """Container for all handlers and hooks injected into Coordinator.

    This dataclass decouples the Coordinator from handler creation logic,
    allowing handlers to be created externally and injected.
    """

    lifecycle_handlers: Mapping[ScheduleType, SessionLifecycleHandler]
    promotion_handlers: Mapping[ScheduleType, SessionPromotionHandler]
    kernel_handlers: Mapping[ScheduleType, KernelLifecycleHandler]


@dataclass
class CoordinatorHandlersArgs:
    """Arguments for creating CoordinatorHandlers."""

    provisioner: SessionProvisioner
    launcher: SessionLauncher
    terminator: SessionTerminator
    repository: SchedulerRepository
    valkey_schedule: ValkeyScheduleClient
    scheduling_controller: SchedulingController


def create_coordinator_handlers(args: CoordinatorHandlersArgs) -> CoordinatorHandlers:
    """Create all handlers and hooks for the Coordinator.

    This factory function centralizes handler creation, decoupling the
    Coordinator from the details of handler instantiation.
    """
    lifecycle_handlers = _create_lifecycle_handlers(args)
    promotion_handlers = _create_promotion_handlers(args)
    kernel_handlers = _create_kernel_handlers(args)

    return CoordinatorHandlers(
        lifecycle_handlers=lifecycle_handlers,
        promotion_handlers=promotion_handlers,
        kernel_handlers=kernel_handlers,
    )


def _create_lifecycle_handlers(
    args: CoordinatorHandlersArgs,
) -> Mapping[ScheduleType, SessionLifecycleHandler]:
    """Create lifecycle handlers mapping."""
    return {
        ScheduleType.SCHEDULE: ScheduleSessionsLifecycleHandler(
            args.provisioner,
            args.repository,
        ),
        ScheduleType.DEPRIORITIZE: DeprioritizeSessionsLifecycleHandler(
            args.repository,
        ),
        ScheduleType.CHECK_PRECONDITION: CheckPreconditionLifecycleHandler(
            args.launcher,
            args.repository,
        ),
        ScheduleType.START: StartSessionsLifecycleHandler(
            args.launcher,
            args.repository,
        ),
        ScheduleType.TERMINATE: TerminateSessionsLifecycleHandler(
            args.terminator,
            args.repository,
        ),
        ScheduleType.SWEEP: SweepSessionsLifecycleHandler(
            args.repository,
        ),
    }


def _create_promotion_handlers(
    args: CoordinatorHandlersArgs,
) -> Mapping[ScheduleType, SessionPromotionHandler]:
    """Create promotion handlers mapping."""
    return {
        ScheduleType.CHECK_PULLING_PROGRESS: PromoteToPreparedPromotionHandler(),
        ScheduleType.CHECK_CREATING_PROGRESS: PromoteToRunningPromotionHandler(),
        ScheduleType.CHECK_TERMINATING_PROGRESS: PromoteToTerminatedPromotionHandler(),
        ScheduleType.CHECK_RUNNING_SESSION_TERMINATION: DetectTerminationPromotionHandler(),
    }


def _create_kernel_handlers(
    args: CoordinatorHandlersArgs,
) -> Mapping[ScheduleType, KernelLifecycleHandler]:
    """Create kernel handlers mapping."""
    return {
        ScheduleType.SWEEP_STALE_KERNELS: SweepStaleKernelsKernelHandler(
            args.terminator,
        ),
    }
