import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
import sqlalchemy as sa
import yarl
from sqlalchemy.orm.exc import NoResultFound

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
    SessionPreparingAnycastEvent,
    SessionScheduledAnycastEvent,
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
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.registry import AgentRegistry

from ...models.endpoint import EndpointRow
from ...models.routing import RouteStatus, RoutingRow
from ...models.session import KernelLoadingStrategy, SessionRow
from ...models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionEventHandler:
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    _idle_checker_host: IdleCheckerHost

    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        event_dispatcher_plugin_ctx: EventDispatcherPluginContext,
        idle_checker_host: IdleCheckerHost,
    ) -> None:
        self._registry = registry
        self._db = db
        self._event_dispatcher_plugin_ctx = event_dispatcher_plugin_ctx
        self._idle_checker_host = idle_checker_host

    async def _handle_started_or_cancelled(
        self,
        context: None,
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
        log.info("handle_session_started: ev:{} s:{}", event.event_name(), event.session_id)
        await self._handle_started_or_cancelled(None, source, event)
        await self._idle_checker_host.dispatch_session_status_event(
            event.session_id, SessionStatus.RUNNING
        )
        await self._event_dispatcher_plugin_ctx.handle_event(context, source, event)

    async def handle_session_cancelled(
        self,
        context: None,
        source: AgentId,
        event: SessionCancelledAnycastEvent,
    ) -> None:
        """
        Update the database according to the session-level lifecycle events
        published by the manager.
        """
        log.info("handle_session_cancelled: ev:{} s:{}", event.event_name(), event.session_id)
        await self._handle_started_or_cancelled(None, source, event)

    async def handle_session_terminating(
        self,
        context: None,
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
        context: None,
        source: AgentId,
        event: SessionTerminatedAnycastEvent,
    ) -> None:
        await self._registry.clean_session(event.session_id)
        await self.invoke_session_callback(None, source, event)

    async def handle_destroy_session(
        self,
        context: None,
        source: AgentId,
        event: DoTerminateSessionEvent,
    ) -> None:
        async with self._registry.db.begin_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess, event.session_id, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
            )
        await self._registry.destroy_session(
            session,
            forced=False,
            reason=event.reason or KernelLifecycleEventReason.KILLED_BY_EVENT,
        )

    async def handle_batch_result(
        self,
        context: None,
        source: AgentId,
        event: SessionSuccessAnycastEvent | SessionFailureAnycastEvent,
    ) -> None:
        """
        Update the database according to the batch-job completion results
        """
        match event:
            case SessionSuccessAnycastEvent(
                session_id=session_id, reason=reason, exit_code=exit_code
            ):
                await SessionRow.set_session_result(
                    self._db, session_id, success=True, exit_code=exit_code
                )
            case SessionFailureAnycastEvent(
                session_id=session_id, reason=reason, exit_code=exit_code
            ):
                await SessionRow.set_session_result(
                    self._db, session_id, success=False, exit_code=exit_code
                )
        async with self._db.begin_session() as db_sess:
            try:
                session = await SessionRow.get_session(
                    db_sess,
                    event.session_id,
                    kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                )
            except SessionNotFound:
                return
        await self._registry.destroy_session(
            session,
            reason=reason,
        )

        await self.invoke_session_callback(None, source, event)

    async def invoke_session_callback(
        self,
        context: None,
        source: AgentId,
        event: (
            SessionEnqueuedAnycastEvent
            | SessionScheduledAnycastEvent
            | SessionCheckingPrecondAnycastEvent
            | SessionPreparingAnycastEvent
            | SessionStartedAnycastEvent
            | SessionCancelledAnycastEvent
            | SessionTerminatingAnycastEvent
            | SessionTerminatedAnycastEvent
            | SessionSuccessAnycastEvent
            | SessionFailureAnycastEvent
        ),
    ) -> None:
        log.info("INVOKE_SESSION_CALLBACK (source:{}, event:{})", source, event)
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

        try:
            # Update routing status
            # TODO: Check session health
            if session.session_type == SessionTypes.INFERENCE:

                async def _update() -> None:
                    async with self._db.begin_session() as db_sess:
                        route = await RoutingRow.get_by_session(
                            db_sess, session.id, load_endpoint=True
                        )
                        endpoint = await EndpointRow.get(db_sess, route.endpoint, load_routes=True)
                        match event:
                            case SessionCancelledAnycastEvent():
                                update_data: dict[str, Any] = {
                                    "status": RouteStatus.FAILED_TO_START
                                }
                                if "error" in session.status_data:
                                    if session.status_data["error"]["name"] == "MultiAgentError":
                                        errors = session.status_data["error"]["collection"]
                                    else:
                                        errors = [session.status_data["error"]]
                                    update_data["error_data"] = {
                                        "type": "session_cancelled",
                                        "errors": errors,
                                        "session_id": session.id,
                                    }
                                query = (
                                    sa.update(RoutingRow)
                                    .values(update_data)
                                    .where(RoutingRow.id == route.id)
                                )
                                await db_sess.execute(query)
                                query = (
                                    sa.update(EndpointRow)
                                    .values({"retries": endpoint.retries + 1})
                                    .where(EndpointRow.id == endpoint.id)
                                )
                                await db_sess.execute(query)
                        await db_sess.commit()

                await execute_with_retry(_update)

                async def _clear_error() -> None:
                    async with self._db.begin_session() as db_sess:
                        route = await RoutingRow.get_by_session(
                            db_sess, session.id, load_endpoint=True
                        )
                        endpoint = await EndpointRow.get(db_sess, route.endpoint, load_routes=True)

                        query = sa.select([sa.func.count("*")]).where(
                            (RoutingRow.endpoint == endpoint.id)
                            & (RoutingRow.status == RouteStatus.HEALTHY)
                        )
                        healthy_routes = await db_sess.scalar(query)
                        if endpoint.replicas == healthy_routes:
                            query = (
                                sa.update(EndpointRow)
                                .where(EndpointRow.id == endpoint.id)
                                .values({"retries": 0})
                            )
                            await db_sess.execute(query)
                            query = sa.delete(RoutingRow).where(
                                (RoutingRow.endpoint == endpoint.id)
                                & (RoutingRow.status == RouteStatus.FAILED_TO_START)
                            )
                            await db_sess.execute(query)

                await execute_with_retry(_clear_error)
        except NoResultFound:
            pass  # Cases when we try to create a inference session for validation (/services/_/try API)
        except Exception:
            log.exception("error while updating route status:")

        if (callback_url := session.callback_url) is None:
            return

        data = {
            "type": "session_lifecycle",
            "event": event.event_name().removeprefix("session_"),
            "session_id": str(event.session_id),
            "when": datetime.now(timezone.utc).isoformat(),
        }

        self._registry.webhook_ptask_group.create_task(
            _make_session_callback(data, callback_url),
        )

    async def handle_execution_started(
        self,
        context: None,
        source: AgentId,
        event: ExecutionStartedAnycastEvent,
    ) -> None:
        await self._idle_checker_host.dispatch_session_execution_status_event(
            event.session_id, event.execution_status()
        )

    async def handle_execution_finished(
        self,
        context: None,
        source: AgentId,
        event: ExecutionFinishedAnycastEvent,
    ) -> None:
        await self._idle_checker_host.dispatch_session_execution_status_event(
            event.session_id, event.execution_status()
        )

    async def handle_execution_timeout(
        self,
        context: None,
        source: AgentId,
        event: ExecutionTimeoutAnycastEvent,
    ) -> None:
        await self._idle_checker_host.dispatch_session_execution_status_event(
            event.session_id, event.execution_status()
        )

    async def handle_execution_cancelled(
        self,
        context: None,
        source: AgentId,
        event: ExecutionCancelledAnycastEvent,
    ) -> None:
        await self._idle_checker_host.dispatch_session_execution_status_event(
            event.session_id, event.execution_status()
        )


async def _make_session_callback(data: dict[str, Any], url: yarl.URL) -> None:
    log_func = log.info
    log_msg: str = ""
    log_fmt: str = ""
    log_arg: Any = None
    begin = time.monotonic()
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
        ) as session:
            try:
                async with session.post(url, json=data) as response:
                    if response.content_length is not None and response.content_length > 0:
                        log_func = log.warning
                        log_msg = "warning"
                        log_fmt = (
                            "{3[0]} {3[1]} - the callback response body was not empty! "
                            "(len: {3[2]:,} bytes)"
                        )
                        log_arg = (response.status, response.reason, response.content_length)
                    else:
                        log_msg = "result"
                        log_fmt = "{3[0]} {3[1]}"
                        log_arg = (response.status, response.reason)
            except aiohttp.ClientError as e:
                log_func = log.warning
                log_msg, log_fmt, log_arg = "failed", "{3}", repr(e)
    except asyncio.CancelledError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "cancelled", "elapsed_time = {3:.6f}", time.monotonic() - begin
    except asyncio.TimeoutError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "timeout", "elapsed_time = {3:.6f}", time.monotonic() - begin
    finally:
        log_func(
            "Session lifecycle callback " + log_msg + " (e:{0}, s:{1}, url:{2}): " + log_fmt,
            data["event"],
            data["session_id"],
            url,
            log_arg,
        )
