"""Registry for status-based transition hooks.

Maps session statuses to their corresponding hook implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .status import (
    RunningHookDependencies,
    RunningTransitionHook,
    StatusTransitionHook,
    TerminatedHookDependencies,
    TerminatedTransitionHook,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class HookRegistryArgs:
    """Arguments for creating HookRegistry."""

    scheduler_repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    agent_client_pool: AgentClientPool
    event_producer: EventProducer


class HookRegistry:
    """Registry for status-based transition hooks.

    Provides hooks for specific session status transitions.
    Returns None for statuses that don't require hook execution.
    """

    _status_hooks: dict[SessionStatus, StatusTransitionHook]

    def __init__(self, args: HookRegistryArgs) -> None:
        self._status_hooks = {}
        self._initialize_hooks(args)

    def _initialize_hooks(self, args: HookRegistryArgs) -> None:
        """Initialize status-based hooks."""
        # RUNNING transition hook
        running_deps = RunningHookDependencies(
            scheduler_repository=args.scheduler_repository,
            agent_client_pool=args.agent_client_pool,
            deployment_repository=args.deployment_repository,
            event_producer=args.event_producer,
        )
        self._status_hooks[SessionStatus.RUNNING] = RunningTransitionHook(running_deps)

        # TERMINATED transition hook
        terminated_deps = TerminatedHookDependencies(
            deployment_repository=args.deployment_repository,
            event_producer=args.event_producer,
        )
        self._status_hooks[SessionStatus.TERMINATED] = TerminatedTransitionHook(terminated_deps)

    def get_hook(self, status: SessionStatus) -> StatusTransitionHook | None:
        """Get the hook for a specific status transition.

        Args:
            status: The target status of the transition

        Returns:
            The hook for this status, or None if no hook is needed
        """
        hook = self._status_hooks.get(status)
        if hook:
            log.trace("Found hook {} for status {}", hook.__class__.__name__, status)
        return hook
