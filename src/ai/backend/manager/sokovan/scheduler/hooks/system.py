"""
Hook for system session type.
System sessions don't require special handling during state transitions.
"""

from __future__ import annotations

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.scheduler.types import SessionTransitionData, SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class SystemSessionHook(AbstractSessionHook):
    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        log.debug(
            "System session {} transitioning to RUNNING",
            session.session_id,
        )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        log.debug(
            "System session {} transitioning to TERMINATED",
            session.session_id,
        )

    async def on_transition_to_running_v2(self, session: SessionWithKernels) -> None:
        log.debug(
            "System session {} transitioning to RUNNING",
            session.session_info.identity.id,
        )

    async def on_transition_to_terminated_v2(self, session: SessionWithKernels) -> None:
        log.debug(
            "System session {} transitioning to TERMINATED",
            session.session_info.identity.id,
        )
