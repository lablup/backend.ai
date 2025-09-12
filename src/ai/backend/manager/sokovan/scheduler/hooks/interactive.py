"""
Hook for interactive session type.
Interactive sessions don't require special handling during state transitions.
"""

import logging

from ai.backend.logging import BraceStyleAdapter

from ..types import SessionTransitionData
from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InteractiveSessionHook(AbstractSessionHook):
    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        log.debug(
            "Interactive session {} transitioning to RUNNING",
            session.session_id,
        )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        log.debug(
            "Interactive session {} transitioning to TERMINATED",
            session.session_id,
        )
