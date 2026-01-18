"""
Hook for inference session type.
Handles model serving operations like route creation and deletion.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.model_serving.anycast import (
    EndpointRouteListUpdatedEvent,
)
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

from .base import AbstractSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class InferenceSessionHook(AbstractSessionHook):
    _repository: DeploymentRepository
    _event_producer: EventProducer

    def __init__(
        self,
        repository: DeploymentRepository,
        event_producer: EventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        match status:
            case SessionStatus.RUNNING:
                await self._on_transition_to_running(session)
            case SessionStatus.TERMINATED:
                await self._on_transition_to_terminated(session)
            case _:
                log.debug(
                    "Inference session {} transitioning to {}",
                    session.session_info.identity.id,
                    status,
                )

    async def _get_endpoint_id_from_session(self, session_id: SessionId) -> Optional[uuid.UUID]:
        """
        Extract endpoint ID from session by looking up the associated route.

        Args:
            session_id: Session ID

        Returns:
            Endpoint ID if found, None otherwise
        """
        try:
            endpoint_id = await self._repository.get_endpoint_id_by_session(session_id)
            if not endpoint_id:
                log.warning(
                    "No endpoint ID found for session {}",
                    session_id,
                )
            return endpoint_id
        except Exception as e:
            log.error(
                "Error getting endpoint ID for session {}: {}",
                session_id,
                e,
            )
            return None

    async def _on_transition_to_running(self, session: SessionWithKernels) -> None:
        """Handle route creation when inference session starts running."""
        session_id = session.session_info.identity.id
        log.info(
            "Creating model service route for inference session {}",
            session_id,
        )

        # Get endpoint ID from session metadata
        endpoint_id = await self._get_endpoint_id_from_session(session_id)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session_id,
            )
            return

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "setup_route",
                success_detail=f"Set up route for endpoint {endpoint_id}",
            ):
                try:
                    # Update route info
                    await self._repository.update_endpoint_route_info(endpoint_id)

                    # Send event to app proxy
                    await self._event_producer.anycast_event(
                        EndpointRouteListUpdatedEvent(endpoint_id)
                    )

                    log.info(
                        "Successfully updated route info and notified app proxy for endpoint {} (session {})",
                        endpoint_id,
                        session_id,
                    )
                except Exception as e:
                    log.exception(
                        "Unexpected error updating route info for endpoint {} (session {}): {}",
                        endpoint_id,
                        session_id,
                        e,
                    )
                    # Don't fail the session transition, just log the error

    async def _on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        """Handle route deletion when inference session terminates."""
        session_id = session.session_info.identity.id
        log.info(
            "Deleting model service route for inference session {}",
            session_id,
        )

        # Get endpoint ID from session metadata
        endpoint_id = await self._get_endpoint_id_from_session(session_id)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session_id,
            )
            return

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_termination",
            success_detail="Session termination finalized",
        ):
            with recorder.step(
                "cleanup_route",
                success_detail=f"Cleaned up route for endpoint {endpoint_id}",
            ):
                try:
                    # Update route info (removal)
                    await self._repository.update_endpoint_route_info(endpoint_id)

                    # Send event to app proxy
                    await self._event_producer.anycast_event(
                        EndpointRouteListUpdatedEvent(endpoint_id)
                    )

                    log.info(
                        "Successfully updated route info and notified app proxy of route removal for endpoint {} (session {})",
                        endpoint_id,
                        session_id,
                    )
                except Exception as e:
                    log.exception(
                        "Unexpected error updating route info for endpoint {} (session {}): {}",
                        endpoint_id,
                        session_id,
                        e,
                    )
                    # Don't fail the session transition, just log the error
