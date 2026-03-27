from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.client.v2.streaming_types import SSEConnection

_EVENTS_BASE = "/events"


class EventStreamClient(BaseDomainClient):
    """Client for SSE-based event streaming endpoints.

    Provides async context managers that yield :class:`SSEConnection`
    instances for consuming Server-Sent Events from the ``/events``
    endpoints.
    """

    # -----------------------------------------------------------------------
    # SSE — Session events
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def subscribe_session_events(
        self,
        *,
        session_name: str = "*",
        owner_access_key: str | None = None,
        session_id: UUID | None = None,
        group_name: str = "*",
        scope: str = "*",
    ) -> AsyncIterator[SSEConnection]:
        """Subscribe to session lifecycle events via SSE.

        Yields an :class:`SSEConnection` that produces
        :class:`~ai.backend.client.v2.streaming_types.SSEEvent` instances
        for session and kernel lifecycle transitions.

        Args:
            session_name: Session name filter (``"*"`` for all).
            owner_access_key: Owner access key for the session.
            session_id: Session UUID (overrides *session_name* and
                *owner_access_key* when set).
            group_name: Group name filter (``"*"`` for all).
            scope: Comma-separated scope, e.g. ``"session,kernel"``
                (``"*"`` for all).
        """
        params: dict[str, str] = {
            "name": session_name,
            "group": group_name,
            "scope": scope,
        }
        if owner_access_key is not None:
            params["ownerAccessKey"] = owner_access_key
        if session_id is not None:
            params["sessionId"] = str(session_id)
        async with self._client.sse_connect(
            f"{_EVENTS_BASE}/session",
            params=params,
        ) as sse:
            yield sse

    # -----------------------------------------------------------------------
    # SSE — Background task events
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def subscribe_background_task_events(
        self,
        task_id: UUID,
    ) -> AsyncIterator[SSEConnection]:
        """Subscribe to background-task progress events via SSE.

        Yields an :class:`SSEConnection` that produces
        :class:`~ai.backend.client.v2.streaming_types.SSEEvent` instances
        for background task progress, completion, and failure.

        Args:
            task_id: UUID of the background task to monitor.
        """
        async with self._client.sse_connect(
            f"{_EVENTS_BASE}/background-task",
            params={"taskId": str(task_id)},
        ) as sse:
            yield sse
