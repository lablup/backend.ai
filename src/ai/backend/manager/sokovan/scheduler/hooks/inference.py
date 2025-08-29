"""
Hook for inference session type.
Handles model serving operations like route creation and deletion.
"""

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from ..types import SessionTransitionData
from .base import SessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InferenceSessionHook(SessionHook):
    _repository: DeploymentRepository

    def __init__(self, repository: DeploymentRepository) -> None:
        self._repository = repository

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
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

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
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
