from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING, Any, Mapping, Optional

import sqlalchemy as sa
from sqlalchemy.orm import load_only

from ai.backend.common.events.dispatcher import AbstractEvent
from ai.backend.common.events.event_types.kernel.broadcast import (
    BaseKernelEvent,
    KernelCancelledBroadcastEvent,
    KernelCreatingBroadcastEvent,
    KernelPreparingBroadcastEvent,
    KernelPullingBroadcastEvent,
    KernelStartedBroadcastEvent,
    KernelTerminatedBroadcastEvent,
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    BaseSessionEvent,
    SchedulingBroadcastEvent,
    SessionCancelledBroadcastEvent,
    SessionEnqueuedBroadcastEvent,
    SessionFailureBroadcastEvent,
    SessionScheduledBroadcastEvent,
    SessionStartedBroadcastEvent,
    SessionSuccessBroadcastEvent,
    SessionTerminatedBroadcastEvent,
    SessionTerminatingBroadcastEvent,
)
from ai.backend.common.events.hub import WILDCARD, EventPropagator
from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from aiohttp_sse import EventSourceResponse

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionEventPropagator(EventPropagator):
    """
    SessionEventPropagator handles session and kernel events for SSE streaming.
    It filters events based on user permissions and session criteria.
    """

    _id: uuid.UUID
    _queue: asyncio.Queue[Optional[AbstractEvent]]
    _closed: bool
    _response: EventSourceResponse
    _db: ExtendedAsyncSAEngine
    _filters: Mapping[str, Any]
    _closed_lock: asyncio.Lock

    def __init__(
        self,
        response: EventSourceResponse,
        db: ExtendedAsyncSAEngine,
        filters: Mapping[str, Any],
    ) -> None:
        """
        Initialize the SessionEventPropagator.

        :param response: SSE response object for streaming events
        :param db: Database connection for fetching session data
        :param filters: Event filtering criteria containing:
            - user_role: User role for permission checks
            - user_uuid: User UUID for ownership checks
            - domain_name: Domain name for domain filtering
            - group_id: Group ID for group filtering
            - session_name: Session name filter
            - session_id: Session ID filter
            - access_key: Access key for session ownership
            - scope: Event scope filter ("*", "session", "kernel")
        """
        self._id = uuid.uuid4()
        self._queue = asyncio.Queue()
        self._closed = False
        self._response = response
        self._db = db
        self._filters = filters
        self._closed_lock = asyncio.Lock()

    def id(self) -> uuid.UUID:
        """Get the unique identifier for the propagator."""
        return self._id

    async def propagate_event(self, event: AbstractEvent) -> None:
        """Propagate an event to the SSE stream if it passes filtering."""
        if self._closed:
            return

        # Get event data based on event type
        data = await self._get_event_data(event)
        if data is None:
            log.warning("Could not fetch the domain object for {!r}", event)
            return
        event_name, event_data = data

        # Apply permission and session filters
        if not await self._should_send_event(event_data):
            return

        # Build response data
        response_data = {
            "reason": event_data.get("reason", ""),
            "sessionName": event_data.get("session_name", ""),
            "ownerAccessKey": event_data.get("access_key", ""),
            "sessionId": str(event_data.get("session_id", "")),
            "exitCode": event_data.get("exit_code"),
        }

        # Add kernel-specific fields if present
        if kernel_id := event_data.get("kernel_id"):
            response_data["kernelId"] = str(kernel_id)
        if cluster_role := event_data.get("cluster_role"):
            response_data["clusterRole"] = cluster_role
        if cluster_idx := event_data.get("cluster_idx"):
            response_data["clusterIdx"] = cluster_idx

        try:
            await self._response.send(dump_json_str(response_data), event=event_name)
        except Exception as e:
            log.warning("Failed to send SSE event: {}", e)
            await self.close()

    async def _get_event_data(
        self, event: AbstractEvent
    ) -> Optional[tuple[str, Mapping[str, Any]]]:
        """Get event data from database based on event type."""
        match event:
            case SchedulingBroadcastEvent():
                return await self._fetch_session_data(event)
            case (
                KernelPreparingBroadcastEvent()
                | KernelPullingBroadcastEvent()
                | KernelCreatingBroadcastEvent()
                | KernelStartedBroadcastEvent()
                | KernelCancelledBroadcastEvent()
                | KernelTerminatingBroadcastEvent()
                | KernelTerminatedBroadcastEvent()
            ):
                return await self._fetch_kernel_data(event)
            case (
                SessionEnqueuedBroadcastEvent()
                | SessionScheduledBroadcastEvent()
                | SessionStartedBroadcastEvent()
                | SessionCancelledBroadcastEvent()
                | SessionTerminatingBroadcastEvent()
                | SessionTerminatedBroadcastEvent()
                | SessionSuccessBroadcastEvent()
                | SessionFailureBroadcastEvent()
            ):
                return await self._fetch_session_data(event)
            case _:
                log.debug("Unknown event type: {}", type(event))
                return None

    async def _fetch_kernel_data(
        self, event: BaseKernelEvent
    ) -> Optional[tuple[str, Mapping[str, Any]]]:
        """Fetch kernel data from database."""
        try:
            from ai.backend.manager.models import kernels

            async with self._db.begin_readonly(isolation_level="READ COMMITTED") as conn:
                query = (
                    sa.select([
                        kernels.c.id,
                        kernels.c.session_id,
                        kernels.c.session_name,
                        kernels.c.access_key,
                        kernels.c.cluster_role,
                        kernels.c.cluster_idx,
                        kernels.c.domain_name,
                        kernels.c.group_id,
                        kernels.c.user_uuid,
                    ])
                    .select_from(kernels)
                    .where(kernels.c.id == event.kernel_id)
                )
                result = await conn.execute(query)
                row = result.first()
                if row is None:
                    return None

                data = dict(row._mapping)
                data["kernel_id"] = data["id"]
                data["reason"] = getattr(event, "reason", "")
                data["exit_Code"] = getattr(event, "exit_code", None)
                return event.event_name(), data
        except Exception as e:
            log.warning("Failed to fetch kernel data for event {}: {}", event.kernel_id, e)
            return None

    async def _fetch_session_data(
        self, event: BaseSessionEvent | SchedulingBroadcastEvent
    ) -> Optional[tuple[str, Mapping[str, Any]]]:
        """Fetch session data from database."""
        event_name = event.event_name()
        try:
            from ai.backend.manager.models.session import SessionRow

            async with self._db.begin_readonly_session(
                isolation_level="READ COMMITTED"
            ) as db_session:
                query = (
                    sa.select(SessionRow)
                    .where(SessionRow.id == event.session_id)
                    .options(
                        load_only(
                            SessionRow.id,
                            SessionRow.name,
                            SessionRow.access_key,
                            SessionRow.domain_name,
                            SessionRow.group_id,
                            SessionRow.user_uuid,
                        )
                    )
                )
                row = await db_session.scalar(query)
                if row is None:
                    return None

                data = {
                    "session_id": row.id,
                    "session_name": row.name,
                    "access_key": row.access_key,
                    "domain_name": row.domain_name,
                    "group_id": row.group_id,
                    "user_uuid": row.user_uuid,
                }
                if isinstance(event, SchedulingBroadcastEvent):
                    data["status"] = event.status_transition
                    status_to_evname = {
                        "RUNNING": "started",
                    }
                    event_name = "session_" + status_to_evname.get(
                        event.status_transition, event.status_transition.lower()
                    )
                data["reason"] = getattr(event, "reason", "")
                data["exit_Code"] = getattr(event, "exit_code", None)
                return event_name, data
        except Exception as e:
            log.warning("Failed to fetch session data for event {}: {}", event.session_id, e)
            return None

    async def _should_send_event(self, event_data: Mapping[str, Any]) -> bool:
        """Check if event should be sent based on filters."""
        from ai.backend.manager.models import UserRole

        user_role = self._filters.get("user_role")
        user_uuid = self._filters.get("user_uuid")
        domain_name = self._filters.get("domain_name")
        group_id = self._filters.get("group_id")
        session_name = self._filters.get("session_name")
        session_id = self._filters.get("session_id")
        access_key = self._filters.get("access_key")

        # Domain filtering for USER and ADMIN roles
        if user_role in (UserRole.USER, UserRole.ADMIN):
            if event_data.get("domain_name") != domain_name:
                return False

        # User ownership filtering for USER role
        if user_role == UserRole.USER:
            if event_data.get("user_uuid") != user_uuid:
                return False

        # Group filtering
        if group_id != "*" and event_data.get("group_id") != group_id:
            return False

        # Session ID filtering (takes precedence over name/access key)
        if session_id is not None and session_id != WILDCARD:
            if event_data.get("session_id") != session_id:
                return False
        else:
            # Session name and access key filtering
            if session_name != "*":
                if not (
                    event_data.get("session_name") == session_name
                    and event_data.get("access_key") == access_key
                ):
                    return False

        return True

    async def close(self) -> None:
        """Close the propagator and stop event streaming."""
        async with self._closed_lock:
            if self._closed:
                return
            self._closed = True

        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
