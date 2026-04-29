"""Registry for status-based transition hooks.

Maps session statuses to their corresponding hook implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.data.session.types import SessionStatus

from .status import (
    RunningHookDependencies,
    RunningTransitionHook,
    StatusTransitionHook,
    TerminatedHookDependencies,
    TerminatedTransitionHook,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class HookRegistryArgs:
    """Arguments for creating HookRegistry."""

    agent_client_pool: AgentClientPool


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
            agent_client_pool=args.agent_client_pool,
        )
        self._status_hooks[SessionStatus.RUNNING] = RunningTransitionHook(running_deps)

        # TERMINATED transition hook
        terminated_deps = TerminatedHookDependencies()
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
