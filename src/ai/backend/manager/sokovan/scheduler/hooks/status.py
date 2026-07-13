"""Status-based transition hooks.

Hooks are organized by target status (RUNNING, TERMINATED, etc.)
and internally dispatch to session-type specific logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    SessionId,
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.sokovan import SessionWithKernels
from ai.backend.manager.errors.resource import AgentNotAllocated
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.sokovan.recorder.context import RecorderContext

log = BraceStyleAdapter(logging.getLogger(__name__))


class StatusTransitionHook(ABC):
    """Base class for status-based transition hooks.

    Each subclass handles a specific target status (RUNNING, TERMINATED, etc.)
    and internally dispatches to session-type specific logic.
    """

    @abstractmethod
    async def execute(self, session: SessionWithKernels) -> None:
        """Execute the hook for a session transitioning to this status.

        Args:
            session: The session with kernel information
        """
        raise NotImplementedError


@dataclass
class RunningHookDependencies:
    """Dependencies for RunningTransitionHook."""

    agent_client_pool: AgentClientPool


class RunningTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to RUNNING status.

    Handles:
    - BATCH: Trigger batch execution
    - INFERENCE: no-op — the route coordinator pushes to AppProxy
      synchronously from the health-check handler when a route first
      transitions to HEALTHY, and the long-cycle ``AppProxySyncRouteHandler``
      keeps state convergent as a fallback.

    Note: Resource allocation (occupied_slots) is handled per-kernel at
    kernel RUNNING transition time, not here at session level.
    """

    _deps: RunningHookDependencies

    def __init__(self, deps: RunningHookDependencies) -> None:
        self._deps = deps

    @override
    async def execute(self, session: SessionWithKernels) -> None:
        """Execute RUNNING transition hook.

        Note: Resource allocation is now handled per-kernel at kernel RUNNING
        transition time (in update_kernel_status_running), not here at
        session RUNNING transition time.
        """
        # Session-type specific logic
        session_type = session.session_info.metadata.session_type
        match session_type:
            case SessionTypes.BATCH:
                await self._execute_batch(session)
            case _:
                log.debug(
                    "No specific RUNNING hook for session type {}",
                    session_type,
                )

    async def _execute_batch(self, session: SessionWithKernels) -> None:
        """Trigger batch execution for BATCH sessions."""
        main_kernel = session.main_kernel
        agent_id = AgentId(main_kernel.resource.agent) if main_kernel.resource.agent else None
        if agent_id is None:
            raise ValueError(
                f"Main kernel has no agent assigned for session {session.session_info.identity.id}"
            )

        session_id = session.session_info.identity.id
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "trigger_batch_execution",
                success_detail=f"Triggered batch execution on agent {agent_id}",
            ):
                async with self._deps.agent_client_pool.acquire(agent_id) as client:
                    session_batch_timeout = session.session_info.lifecycle.batch_timeout
                    await client.trigger_batch_execution(
                        session_id,
                        main_kernel.id,
                        main_kernel.runtime.startup_command or "",
                        float(session_batch_timeout) if session_batch_timeout is not None else None,
                    )
        log.info(
            "Successfully triggered batch execution for session {} on agent {}",
            session_id,
            agent_id,
        )


@dataclass
class TerminatedHookDependencies:
    """Dependencies for TerminatedTransitionHook."""

    agent_client_pool: AgentClientPool
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider


class TerminatedTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to TERMINATED status.

    Destroys the session's volatile inter-container network so that
    overlay (MULTI_NODE) and agent-local (SINGLE_NODE) networks do not
    leak after the session terminates. The hook is blocking: on failure
    it propagates so the coordinator keeps the session in TERMINATING and
    the self-healing loop retries the cleanup on the next tick.
    """

    _deps: TerminatedHookDependencies

    def __init__(self, deps: TerminatedHookDependencies) -> None:
        self._deps = deps

    @override
    async def execute(self, session: SessionWithKernels) -> None:
        """Execute TERMINATED transition hook."""
        await self._destroy_network(session)

    async def _destroy_network(self, session: SessionWithKernels) -> None:
        network = session.session_info.network
        if network.network_type != NetworkType.VOLATILE or network.network_id is None:
            return
        network_id = network.network_id
        session_id = session.session_info.identity.id
        cluster_mode = ClusterMode(session.session_info.resource.cluster_mode)

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "terminate_cleanup",
            success_detail="Volatile inter-container network destroyed",
        ):
            with recorder.step(
                "destroy_network",
                success_detail=f"Destroyed {cluster_mode.value} network {network_id}",
            ):
                if cluster_mode == ClusterMode.SINGLE_NODE:
                    await self._destroy_local_network(session, network_id)
                elif cluster_mode == ClusterMode.MULTI_NODE:
                    await self._destroy_multinode_network(session_id, network_id)

    async def _destroy_local_network(self, session: SessionWithKernels, network_id: str) -> None:
        session_id = session.session_info.identity.id
        agent_id = session.main_kernel.resource.agent
        if agent_id is None:
            raise AgentNotAllocated(f"Main kernel has no agent assigned for session {session_id}")
        async with self._deps.agent_client_pool.acquire(AgentId(agent_id)) as client:
            try:
                await client.destroy_local_network(network_id)
            except Exception:
                log.exception(
                    "Failed to destroy local network on agent for session. "
                    "Session ID: {}, Network ID: {}, Agent ID: {}",
                    session_id,
                    network_id,
                    agent_id,
                )
                raise

    async def _destroy_multinode_network(self, session_id: SessionId, network_id: str) -> None:
        """Tear down the session's multi-node network across every registered driver.

        The driver is NOT re-derived from ``default_driver`` here: the launcher picks it
        *dynamically* from the member agents' runtime (a containerd agent gets 'cni', a docker
        agent gets 'overlay'), and can diverge from the configured default -- so destroying by the
        configured driver leaks the network of every session whose agents needed the other one.
        That was the failure: create via 'cni' (dynamic) but destroy via 'overlay' (config default,
        which is 'overlay' out of the box) meant the CNI subnet/VNI/etcd state was never released,
        and the pool exhausted after ~4096 multi-node sessions.

        Each ``destroy_network`` is idempotent and a no-op on a session it does not own -- the CNI
        driver keys off its own etcd session meta, the overlay driver off the Docker network's
        existence -- so calling every driver reclaims exactly the one that created this session,
        without the manager having to remember (or re-derive) which one that was.
        """
        errors: list[tuple[str, BaseException]] = []
        for driver, plugin in self._deps.network_plugin_ctx.plugins.items():
            try:
                await plugin.destroy_network(network_id=network_id)
            except Exception as e:
                log.exception(
                    "Failed to destroy the '{}' network for session {} (network {})",
                    driver,
                    session_id,
                    network_id,
                )
                errors.append((driver, e))
        if errors:
            # The hook is blocking: propagate so the coordinator keeps retrying rather than
            # silently leaking the network state of a session that did not fully clean up.
            raise errors[0][1]
