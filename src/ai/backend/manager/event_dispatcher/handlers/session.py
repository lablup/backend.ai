import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp
import yarl

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.events.event_types.session.anycast import (
    DoTerminateSessionEvent,
    ExecutionCancelledAnycastEvent,
    ExecutionFinishedAnycastEvent,
    ExecutionStartedAnycastEvent,
    ExecutionTimeoutAnycastEvent,
    SessionCancelledAnycastEvent,
    SessionCheckingPrecondAnycastEvent,
    SessionEnqueuedAnycastEvent,
    SessionFailureAnycastEvent,
    SessionStartedAnycastEvent,
    SessionSuccessAnycastEvent,
    SessionTerminatedAnycastEvent,
    SessionTerminatingAnycastEvent,
)
from ai.backend.common.events.kernel import (
    KernelLifecycleEventReason,
)
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.session.row import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)

log = StructuredLogger(logging.getLogger(__spec__.name))


class SessionEventHandler:
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    _scheduling_controller: SchedulingController
    _valkey_live: ValkeyLiveClient

    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        event_dispatcher_plugin_ctx: EventDispatcherPluginContext,
        scheduling_controller: SchedulingController,
        valkey_live: ValkeyLiveClient,
    ) -> None:
        self._registry = registry
        self._db = db
        self._event_dispatcher_plugin_ctx = event_dispatcher_plugin_ctx
        self._scheduling_controller = scheduling_controller
        self._valkey_live = valkey_live

    async def _handle_started_or_cancelled(
        self,
        _context: None,
        source: AgentId,
        event: SessionStartedAnycastEvent | SessionCancelledAnycastEvent,
    ) -> None:
        if event.creation_id not in self._registry.session_creation_tracker:
            return
        if tracker := self._registry.session_creation_tracker.get(event.creation_id):
            tracker.set()

        await self.invoke_session_callback(None, source, event)
        if event.creation_id in self._registry.session_creation_tracker:
            del self._registry.session_creation_tracker[event.creation_id]

    async def handle_session_started(
        self,
        context: None,
        source: AgentId,
        event: SessionStartedAnycastEvent,
    ) -> None:
        """
        Update the database according to the session-level lifecycle events
        published by the manager.
        """
        log.trace("session started")
        await self._valkey_live.update_session_last_access(event.session_id)
        await self._handle_started_or_cancelled(None, source, event)
        await self._event_dispatcher_plugin_ctx.handle_event(context, source, event)

    async def handle_session_cancelled(
        self,
        _context: None,
        source: AgentId,
        event: SessionCancelledAnycastEvent,
    ) -> None:
        """
        Update the database according to the session-level lifecycle events
        published by the manager.
        """
        log.trace("session cancelled")
        await self._handle_started_or_cancelled(None, source, event)

    async def handle_session_terminating(
        self,
        _context: None,
        source: AgentId,
        event: SessionTerminatingAnycastEvent,
    ) -> None:
        """
        Update the database according to the session-level lifecycle events
        published by the manager.
        """
        await self.invoke_session_callback(None, source, event)

    async def handle_session_terminated(
        self,
        _context: None,
        source: AgentId,
        event: SessionTerminatedAnycastEvent,
    ) -> None:
        await self._valkey_live.delete_session_last_access(event.session_id)
        await self._registry.clean_session(event.session_id)
        await self.invoke_session_callback(None, source, event)

    async def handle_destroy_session(
        self,
        _context: None,
        _source: AgentId,
        event: DoTerminateSessionEvent,
    ) -> None:
        reason = event.reason or KernelLifecycleEventReason.KILLED_BY_EVENT
        await self._scheduling_controller.mark_sessions_for_termination(
            [event.session_id],
            reason=reason,
            forced=False,
        )

    async def handle_execution_started(
        self,
        _context: None,
        _source: AgentId,
        event: ExecutionStartedAnycastEvent,
    ) -> None:
        await self._valkey_live.mark_session_active(event.session_id)

    async def handle_execution_ended(
        self,
        _context: None,
        _source: AgentId,
        event: (
            ExecutionFinishedAnycastEvent
            | ExecutionTimeoutAnycastEvent
            | ExecutionCancelledAnycastEvent
        ),
    ) -> None:
        await self._valkey_live.update_session_last_access(event.session_id)

    async def handle_batch_result(
        self,
        _context: None,
        source: AgentId,
        event: SessionSuccessAnycastEvent | SessionFailureAnycastEvent,
    ) -> None:
        """
        Update the database according to the batch-job completion results
        """
        reason: KernelLifecycleEventReason
        match event:
            case SessionSuccessAnycastEvent(session_id=session_id, reason=_reason, exit_code=_):
                await SessionRow.set_session_result(self._db, session_id, success=True)
                reason = _reason
            case SessionFailureAnycastEvent(session_id=session_id, reason=_reason, exit_code=_):
                await SessionRow.set_session_result(self._db, session_id, success=False)
                reason = _reason
        await self._scheduling_controller.mark_sessions_for_termination(
            [event.session_id],
            reason=reason,
            forced=False,
        )

        await self.invoke_session_callback(None, source, event)

    async def invoke_session_callback(
        self,
        _context: None,
        source: AgentId,
        event: (
            SessionEnqueuedAnycastEvent
            | SessionCheckingPrecondAnycastEvent
            | SessionStartedAnycastEvent
            | SessionCancelledAnycastEvent
            | SessionTerminatingAnycastEvent
            | SessionTerminatedAnycastEvent
            | SessionSuccessAnycastEvent
            | SessionFailureAnycastEvent
        ),
    ) -> None:
        log.trace("invoking session callback")
        try:
            allow_stale = isinstance(
                event, (SessionCancelledAnycastEvent, SessionTerminatedAnycastEvent)
            )
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    event.session_id,
                    allow_stale=allow_stale,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
        except SessionNotFound:
            return

        if (callback_url := session.callback_url) is None:
            return

        data = {
            "type": "session_lifecycle",
            "event": event.event_name().removeprefix("session_"),
            "session_id": str(event.session_id),
            "when": datetime.now(UTC).isoformat(),
            # Enriched fields — allow the callback receiver to reconstruct
            # intermediate status transitions with accurate timestamps and
            # to read the session result/error details without an extra API call.
            "status_history": dict(session.status_history or {}),
            "result": session.result.name if session.result is not None else None,
            "status_data": dict(session.status_data) if session.status_data is not None else None,
        }

        self._registry.webhook_ptask_group.create_task(
            _make_session_callback(data, callback_url),
        )


async def _make_session_callback(data: dict[str, Any], url: yarl.URL) -> None:
    session_id = str(data["session_id"])
    callback_url = str(url)
    begin = time.monotonic()
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
        ) as session:
            try:
                async with session.post(url, json=data) as response:
                    if response.content_length is not None and response.content_length > 0:
                        log.trace(
                            "session lifecycle callback response body not empty",
                            session_id=session_id,
                            callback_url=callback_url,
                            status_code=response.status,
                            response_bytes=response.content_length,
                        )
                    else:
                        log.trace(
                            "session lifecycle callback sent",
                            session_id=session_id,
                            callback_url=callback_url,
                            status_code=response.status,
                        )
            except aiohttp.ClientError as e:
                log.trace(
                    "session lifecycle callback failed",
                    session_id=session_id,
                    callback_url=callback_url,
                    reason=repr(e),
                )
    except asyncio.CancelledError:
        log.trace(
            "session lifecycle callback cancelled",
            session_id=session_id,
            callback_url=callback_url,
            elapsed_sec=time.monotonic() - begin,
        )
    except TimeoutError:
        log.trace(
            "session lifecycle callback timed out",
            session_id=session_id,
            callback_url=callback_url,
            elapsed_sec=time.monotonic() - begin,
        )
