from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import SchedulerRepository

from .hooks.registry import HookRegistry, HookRegistryArgs
from .launcher.launcher import SessionLauncher
from .provisioner.provisioner import SessionProvisioner
from .terminator.terminator import SessionTerminator


@dataclass
class SchedulerComponents:
    """Container for scheduler components used by Coordinator.

    This dataclass holds references to scheduler sub-components (provisioner, launcher,
    terminator, hook_registry) that are accessed by Coordinator to initialize
    lifecycle handlers.
    """

    provisioner: SessionProvisioner
    launcher: SessionLauncher
    terminator: SessionTerminator
    repository: SchedulerRepository
    config_provider: ManagerConfigProvider
    hook_registry: HookRegistry


def create_scheduler_components(
    provisioner: SessionProvisioner,
    launcher: SessionLauncher,
    terminator: SessionTerminator,
    repository: SchedulerRepository,
    deployment_repository: DeploymentRepository,
    config_provider: ManagerConfigProvider,
    agent_client_pool: AgentClientPool,
    event_producer: EventProducer,
) -> SchedulerComponents:
    """Create SchedulerComponents with all required dependencies."""
    hook_registry = HookRegistry(
        HookRegistryArgs(
            scheduler_repository=repository,
            deployment_repository=deployment_repository,
            agent_client_pool=agent_client_pool,
            event_producer=event_producer,
        )
    )
    return SchedulerComponents(
        provisioner=provisioner,
        launcher=launcher,
        terminator=terminator,
        repository=repository,
        config_provider=config_provider,
        hook_registry=hook_registry,
    )
