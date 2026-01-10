"""
Hook for interactive session type.
Interactive sessions don't require special handling during state transitions.
"""

from __future__ import annotations

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InteractiveSessionHook(AbstractSessionHook):
    async def on_transition_to_running(self, session: SessionWithKernels) -> None:
        log.debug(
            "Interactive session {} transitioning to RUNNING",
            session.session_info.identity.id,
        )

    async def on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        log.debug(
            "Interactive session {} transitioning to TERMINATED",
            session.session_info.identity.id,
        )
