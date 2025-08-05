"""Factory functions for creating scheduler components."""

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.sokovan.scheduler.adapter import ScheduleRepositoryAdapter
from ai.backend.manager.sokovan.scheduler.allocators.repository_allocator import RepositoryAllocator
from ai.backend.manager.sokovan.scheduler.prioritizers.fifo import FIFOSchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.scheduler import (
    Scheduler,
    SchedulerArgs,
)
from ai.backend.manager.sokovan.scheduler.selectors.concentrated import ConcentratedAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduler.validators.concurrency import ConcurrencyValidator
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator


def create_default_scheduler(
    repository: ScheduleRepository, config_provider: ManagerConfigProvider
) -> Scheduler:
    """
    Create a scheduler with default components.

    Args:
        repository: The repository for accessing system data
        config_provider: The manager configuration provider

    Returns:
        A configured Scheduler instance
    """
    # Wrap the repository with the adapter
    scheduler_repo = ScheduleRepositoryAdapter(repository)
    # Create default validator with concurrency rules
    validator = SchedulingValidator([ConcurrencyValidator()])

    # Create default prioritizer (FIFO)
    prioritizer = FIFOSchedulingPrioritizer()

    # Get resource priority from config
    resource_priority = config_provider.config.manager.agent_selection_resource_priority

    # Create default agent selector (Concentrated)
    agent_selector = AgentSelector(ConcentratedAgentSelector(resource_priority))

    # Create default allocator (Repository-based) - uses original repository
    allocator = RepositoryAllocator(repository)

    # Create scheduler args
    args = SchedulerArgs(
        validator=validator,
        prioritizer=prioritizer,
        agent_selector=agent_selector,
        allocator=allocator,
        repository=scheduler_repo,
        config_provider=config_provider,
    )

    return Scheduler(args)
