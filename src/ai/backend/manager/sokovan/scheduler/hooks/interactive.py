"""
Hook for interactive session type.
Interactive sessions don't require special handling during state transitions.
"""

from __future__ import annotations

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InteractiveSessionHook(AbstractSessionHook):
    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        log.debug(
            "Interactive session {} transitioning to {}",
            session.session_info.identity.id,
            status,
        )
