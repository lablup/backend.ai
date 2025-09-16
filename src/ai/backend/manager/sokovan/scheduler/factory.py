"""Factory functions for creating scheduler components."""

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.allocators.repository_allocator import RepositoryAllocator
from ai.backend.manager.sokovan.scheduler.scheduler import (
    Scheduler,
    SchedulerArgs,
)
from ai.backend.manager.sokovan.scheduler.selectors.concentrated import ConcentratedAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduler.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.validators.concurrency import ConcurrencyValidator
from ai.backend.manager.sokovan.scheduler.validators.dependencies import DependenciesValidator
from ai.backend.manager.sokovan.scheduler.validators.domain_resource_limit import (
    DomainResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.group_resource_limit import (
    GroupResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.keypair_resource_limit import (
    KeypairResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.pending_session_count_limit import (
    PendingSessionCountLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.pending_session_resource_limit import (
    PendingSessionResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.reserved_batch import (
    ReservedBatchSessionValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.user_resource_limit import (
    UserResourceLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator
from ai.backend.manager.types import DistributedLockFactory


def create_default_scheduler(
    repository: SchedulerRepository,
    deployment_repository: DeploymentRepository,
    config_provider: ManagerConfigProvider,
    lock_factory: DistributedLockFactory,
    agent_pool: AgentPool,
    network_plugin_ctx: NetworkPluginContext,
    event_producer: EventProducer,
    valkey_schedule: ValkeyScheduleClient,
) -> Scheduler:
    """
    Create a scheduler with default components.

    Args:
        repository: The repository for accessing system data
        deployment_repository: The deployment repository
        config_provider: The manager configuration provider
        lock_factory: Factory for creating distributed locks
        agent_pool: Pool for managing agent clients
        network_plugin_ctx: Network plugin context for network management
        event_producer: Event producer for publishing events
        valkey_schedule: Valkey client for scheduling operations

    Returns:
        A configured Scheduler instance
    """
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
    return Scheduler(
        SchedulerArgs(
            validator=validator,
            sequencer=sequencer,
            agent_selector=agent_selector,
            allocator=allocator,
            repository=repository,
            deployment_repository=deployment_repository,
            config_provider=config_provider,
            lock_factory=lock_factory,
            agent_pool=agent_pool,
            network_plugin_ctx=network_plugin_ctx,
            event_producer=event_producer,
            valkey_schedule=valkey_schedule,
        )
    )
