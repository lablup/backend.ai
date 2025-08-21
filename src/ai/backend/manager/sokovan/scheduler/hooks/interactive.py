"""
Hook for interactive session type.
Interactive sessions don't require special handling during state transitions.
"""

import logging

from ai.backend.logging import BraceStyleAdapter

from ..types import SessionTransitionData
from .base import HookResult, SessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InteractiveSessionHook(SessionHook):
    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        log.debug(
            "Interactive session {} transitioning to RUNNING",
            session.session_id,
        )
        return HookResult.ok("Interactive session ready")

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        log.debug(
            "Interactive session {} transitioning to TERMINATED",
            session.session_id,
        )
        return HookResult.ok("Interactive session cleanup complete")
