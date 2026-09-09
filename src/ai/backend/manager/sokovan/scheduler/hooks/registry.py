"""Registry for status-based transition hooks.

Maps session statuses to their corresponding hook implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.plugin.network import NetworkPluginContext

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
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider


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
        terminated_deps = TerminatedHookDependencies(
            agent_client_pool=args.agent_client_pool,
            network_plugin_ctx=args.network_plugin_ctx,
            config_provider=args.config_provider,
        )
        terminated_hook = TerminatedTransitionHook(terminated_deps)
        self._status_hooks[SessionStatus.TERMINATED] = terminated_hook
        # CANCELLED reaches the same end and owes the same cleanup. The volatile network is
        # created before any kernel starts, so a session cancelled during start-sessions has one
        # and used to keep it: measured on a live node, every cancelled session left its
        # `bai-singlenode-<id>` bridge behind with no containers on it. Docker hands out a /16 per
        # network from a pool of about fifteen, so the leak is self-amplifying -- once the pool is
        # gone the next session's kernels land on a subnet the host already routes elsewhere,
        # become unreachable, fail to start, get cancelled, and leak one more.
        self._status_hooks[SessionStatus.CANCELLED] = terminated_hook

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
