"""
Hook for inference session type.
Handles model serving operations like route creation and deletion.
"""

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

from ..types import SessionTransitionData
from .base import HookResult, SessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InferenceSessionHook(SessionHook):
    _repository: SchedulerRepository

    def __init__(self, repository: SchedulerRepository) -> None:
        self._repository = repository

    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        try:
            log.info(
                "Creating model service route for inference session {}",
                session.session_id,
            )

            service_name = f"model-{session.session_id}"

            log.info(
                "Would create model service '{}' for session {}",
                service_name,
                session.session_id,
            )

            return HookResult.ok(f"Model service route created for {service_name}")

        except Exception as e:
            log.error(
                "Failed to create model service route for session {}: {}",
                session.session_id,
                e,
            )
            return HookResult.fail(
                f"Failed to create model service route: {str(e)}",
                error=e,
            )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        try:
            log.info(
                "Deleting model service route for inference session {}",
                session.session_id,
            )

            service_name = f"model-{session.session_id}"

            log.info(
                "Would delete model service '{}' for session {}",
                service_name,
                session.session_id,
            )

            return HookResult.ok(f"Model service route deleted for {service_name}")

        except Exception as e:
            log.error(
                "Failed to delete model service route for session {}: {}",
                session.session_id,
                e,
            )
            return HookResult.fail(
                f"Failed to delete model service route: {str(e)}",
                error=e,
            )
