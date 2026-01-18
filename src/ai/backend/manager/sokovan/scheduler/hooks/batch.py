"""
Hook for batch session type.
Triggers batch execution when the session transitions to running.
"""

from __future__ import annotations

import logging

from ai.backend.common.types import AgentId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class BatchSessionHook(AbstractSessionHook):
    _agent_client_pool: AgentClientPool

    def __init__(self, agent_client_pool: AgentClientPool) -> None:
        self._agent_client_pool = agent_client_pool

    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        match status:
            case SessionStatus.RUNNING:
                await self._on_transition_to_running(session)
            case SessionStatus.TERMINATED:
                log.debug(
                    "Batch session {} transitioning to TERMINATED",
                    session.session_info.identity.id,
                )
            case _:
                log.debug(
                    "Batch session {} transitioning to {}",
                    session.session_info.identity.id,
                    status,
                )

    async def _on_transition_to_running(self, session: SessionWithKernels) -> None:
        """Handle batch execution trigger using SessionWithKernels."""
        main_kernel = session.main_kernel
        agent_id = AgentId(main_kernel.resource.agent) if main_kernel.resource.agent else None
        if agent_id is None:
            raise ValueError(
                f"Main kernel has no agent assigned for session {session.session_info.identity.id}"
            )

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session.session_info.identity.id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "trigger_batch_execution",
                success_detail=f"Triggered batch execution on agent {agent_id}",
            ):
                async with self._agent_client_pool.acquire(agent_id) as client:
                    await client.trigger_batch_execution(
                        session.session_info.identity.id,
                        main_kernel.id,
                        main_kernel.runtime.startup_command or "",
                        float(session.session_info.lifecycle.batch_timeout or 0),
                    )
        log.info(
            "Successfully triggered batch execution for session {} on agent {}",
            session.session_info.identity.id,
            agent_id,
        )
