"""
Hook for inference session type.
Handles model serving operations like route creation and deletion.
"""

import logging
import uuid
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.model_serving.anycast import (
    EndpointRouteListUpdatedEvent,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from ..types import SessionTransitionData
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

    async def _get_endpoint_id_from_session(
        self, session: SessionTransitionData
    ) -> Optional[uuid.UUID]:
        """
        Extract endpoint ID from session by looking up the associated route.

        Args:
            session: Session transition data

        Returns:
            Endpoint ID if found, None otherwise
        """
        try:
            endpoint_id = await self._repository.get_endpoint_id_by_session(session.session_id)
            if not endpoint_id:
                log.warning(
                    "No endpoint ID found for session {}",
                    session.session_id,
                )
            return endpoint_id
        except Exception as e:
            log.error(
                "Error getting endpoint ID for session {}: {}",
                session.session_id,
                e,
            )
            return None

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        """Handle route creation when inference session starts running."""
        log.info(
            "Creating model service route for inference session {}",
            session.session_id,
        )

        # Get endpoint ID from session metadata
        endpoint_id = await self._get_endpoint_id_from_session(session)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session.session_id,
            )
            return

        try:
            # Update route info in Redis
            await self._repository.update_endpoint_route_info(endpoint_id)

            # Send event to app proxy
            await self._event_producer.anycast_event(EndpointRouteListUpdatedEvent(endpoint_id))

            log.info(
                "Successfully updated route info and notified app proxy for endpoint {} (session {})",
                endpoint_id,
                session.session_id,
            )
        except Exception as e:
            log.exception(
                "Unexpected error updating route info for endpoint {} (session {}): {}",
                endpoint_id,
                session.session_id,
                e,
            )
            # Don't fail the session transition, just log the error

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        """Handle route deletion when inference session terminates."""
        log.info(
            "Deleting model service route for inference session {}",
            session.session_id,
        )

        # Get endpoint ID from session metadata
        endpoint_id = await self._get_endpoint_id_from_session(session)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session.session_id,
            )
            return

        try:
            # Update route info in Redis (removal)
            await self._repository.update_endpoint_route_info(endpoint_id)

            # Send event to app proxy
            await self._event_producer.anycast_event(EndpointRouteListUpdatedEvent(endpoint_id))

            log.info(
                "Successfully updated route info and notified app proxy of route removal for endpoint {} (session {})",
                endpoint_id,
                session.session_id,
            )
        except Exception as e:
            log.exception(
                "Unexpected error updating route info for endpoint {} (session {}): {}",
                endpoint_id,
                session.session_id,
                e,
            )
            # Don't fail the session transition, just log the error
