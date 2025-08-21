"""
Hook for system session type.
System sessions don't require special handling during state transitions.
"""

import logging

from ai.backend.logging import BraceStyleAdapter

from ..types import SessionTransitionData
from .base import HookResult, SessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class SystemSessionHook(SessionHook):
    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        log.debug(
            "System session {} transitioning to RUNNING",
            session.session_id,
        )
        return HookResult.ok("System session ready")

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        log.debug(
            "System session {} transitioning to TERMINATED",
            session.session_id,
        )
        return HookResult.ok("System session cleanup complete")
