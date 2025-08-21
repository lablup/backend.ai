"""
Hook for batch session type.
Triggers batch execution when the session transitions to running.
"""

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentPool

from ..types import SessionTransitionData
from .base import HookResult, SessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class BatchSessionHook(SessionHook):
    _agent_pool: AgentPool

    def __init__(self, agent_pool: AgentPool) -> None:
        self._agent_pool = agent_pool

    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        try:
            main_kernel = session.main_kernel
            async with self._agent_pool._agent_cache.rpc_context(
                main_kernel.agent_id,
                invoke_timeout=30,
                order_key=main_kernel.kernel_id,
            ) as rpc:
                await rpc.call.trigger_batch_execution(
                    str(session.session_id),
                    str(main_kernel.kernel_id),
                    main_kernel.startup_command or "",
                    session.batch_timeout,
                )
            log.info(
                "Successfully triggered batch execution for session {} on agent {}",
                session.session_id,
                main_kernel.agent_id,
            )
            return HookResult.ok("Batch execution triggered")
        except Exception as e:
            log.error(
                "Failed to trigger batch execution for session {}: {}",
                session.session_id,
                e,
            )
            return HookResult.fail(
                f"Failed to trigger batch execution: {str(e)}",
                error=e,
            )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        log.debug(
            "Batch session {} transitioning to TERMINATED",
            session.session_id,
        )
        return HookResult.ok("Batch session cleanup complete")
