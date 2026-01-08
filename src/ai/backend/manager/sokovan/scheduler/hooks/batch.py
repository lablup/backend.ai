"""
Hook for batch session type.
Triggers batch execution when the session transitions to running.
"""

from __future__ import annotations

import logging

from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentPool
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class BatchSessionHook(AbstractSessionHook):
    _agent_pool: AgentPool

    def __init__(self, agent_pool: AgentPool) -> None:
        self._agent_pool = agent_pool

    async def on_transition_to_running(self, session: SessionWithKernels) -> None:
        """Handle batch execution trigger using SessionWithKernels."""
        main_kernel = session.main_kernel
        agent_id = AgentId(main_kernel.resource.agent) if main_kernel.resource.agent else None
        if agent_id is None:
            raise ValueError(
                f"Main kernel has no agent assigned for session {session.session_info.identity.id}"
            )

        async with self._agent_pool._agent_cache.rpc_context(
            agent_id,
            invoke_timeout=30,
            order_key=str(main_kernel.id),
        ) as rpc:
            await rpc.call.trigger_batch_execution(
                str(session.session_info.identity.id),
                str(main_kernel.id),
                main_kernel.runtime.startup_command or "",
                session.session_info.lifecycle.batch_timeout,
            )
        log.info(
            "Successfully triggered batch execution for session {} on agent {}",
            session.session_info.identity.id,
            agent_id,
        )

    async def on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        """Handle batch session termination using SessionWithKernels."""
        log.debug(
            "Batch session {} transitioning to TERMINATED",
            session.session_info.identity.id,
        )
