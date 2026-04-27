from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController

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
    config_provider: ManagerConfigProvider,
    agent_client_pool: AgentClientPool,
    route_controller: RouteController,
) -> SchedulerComponents:
    """Create SchedulerComponents with all required dependencies."""
    hook_registry = HookRegistry(
        HookRegistryArgs(
            agent_client_pool=agent_client_pool,
            route_controller=route_controller,
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
