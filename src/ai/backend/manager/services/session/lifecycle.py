from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import redis.exceptions
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.anycast import (
    SessionStartedAnycastEvent,
    SessionTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SessionTerminatedBroadcastEvent,
)
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_txn_retry,
)

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionLifecycleManager:
    status_set_key = "session_status_update"

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
        event_producer: EventProducer,
        hook_plugin_ctx: HookPluginContext,
        registry: AgentRegistry,
    ) -> None:
        self.db = db
        self.valkey_stat = valkey_stat
        self.valkey_live = valkey_live
        self.event_producer = event_producer
        self.hook_plugin_ctx = hook_plugin_ctx
        self.registry = registry

        def _encode(sid: SessionId) -> bytes:
            return sid.bytes

        def _decode(raw_sid: bytes) -> SessionId:
            return SessionId(UUID(bytes=raw_sid))

        self._encoder = _encode
        self._decoder = _decode

    async def _transit_session_status(
        self,
        db_conn: SAConnection,
        session_id: SessionId,
        status_changed_at: datetime | None = None,
    ) -> tuple[SessionRow, bool]:
        now = status_changed_at or datetime.now(tzutc())

        async def _get_and_transit(
            db_session: SASession,
        ) -> tuple[SessionRow, bool]:
            session_row = await SessionRow.get_session_to_determine_status(db_session, session_id)
            transited = session_row.determine_and_set_status(status_changed_at=now)

            async def _calculate_session_occupied_slots(
                db_session: SASession,
                session_row: SessionRow,
            ) -> None:
                kernel_ids = [k.id for k in session_row.kernels]
                if not kernel_ids:
                    session_row.occupying_slots = ResourceSlot()
                    return
                ra = ResourceAllocationRow.__table__
                effective = sa.func.coalesce(ra.c.used, ra.c.requested)
                stmt = (
                    sa.select(ra.c.slot_name, sa.func.sum(effective).label("total"))
                    .where(
                        ra.c.kernel_id.in_(kernel_ids),
                        ra.c.free_at.is_(None),
                    )
                    .group_by(ra.c.slot_name)
                )
                rows = (await db_session.execute(stmt)).all()
                session_row.occupying_slots = ResourceSlot({r.slot_name: r.total for r in rows})

            match session_row.status:
                case SessionStatus.CREATING:
                    await _calculate_session_occupied_slots(db_session, session_row)
                case SessionStatus.RUNNING if transited:
                    await _calculate_session_occupied_slots(db_session, session_row)

            return session_row, transited

        return await execute_with_txn_retry(_get_and_transit, self.db.begin_session, db_conn)

    async def _post_status_transition(
        self,
        session_row: SessionRow,
    ) -> None:
        match session_row.status:
            case SessionStatus.RUNNING:
                creation_id = session_row.creation_id or ""
                log.debug(
                    "Producing SessionStartedEvent({}, {})",
                    session_row.id,
                    creation_id,
                )
                await self.event_producer.anycast_event(
                    SessionStartedAnycastEvent(session_row.id, creation_id)
                )
                await self.hook_plugin_ctx.notify(
                    "POST_START_SESSION",
                    (
                        session_row.id,
                        session_row.name,
                        session_row.access_key,
                    ),
                )
                match session_row.session_type:
                    case SessionTypes.BATCH:
                        await self.registry.trigger_batch_execution(session_row)
                    case SessionTypes.INFERENCE:
                        await self.handle_inference_session_update(session_row)
            case SessionStatus.TERMINATING:
                if session_row.session_type == SessionTypes.INFERENCE:
                    async with self.db.begin_session() as db_sess:
                        route = await RoutingRow.get_by_session(db_sess, session_row.id)
                        route.status = RouteStatus.TERMINATING
                        await db_sess.commit()
                    await self.handle_inference_session_update(session_row)
            case SessionStatus.TERMINATED:
                if session_row.session_type == SessionTypes.INFERENCE:
                    async with self.db.begin_session() as db_sess:
                        query = sa.delete(RoutingRow).where(RoutingRow.session == session_row.id)
                        await db_sess.execute(query)
                        await db_sess.commit()
                status_info = session_row.main_kernel.status_info or ""
                await self.event_producer.anycast_and_broadcast_event(
                    SessionTerminatedAnycastEvent(session_row.id, status_info),
                    SessionTerminatedBroadcastEvent(session_row.id, status_info),
                )
            case _:
                pass

    async def handle_inference_session_update(self, session: SessionRow) -> None:
        async with self.db.begin_readonly_session() as db_sess:
            route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
        await self.registry.notify_endpoint_route_update_to_appproxy(route.endpoint)

    async def transit_session_status(
        self,
        session_ids: Iterable[SessionId],
        status_changed_at: datetime | None = None,
    ) -> list[tuple[SessionRow, bool]]:
        if not session_ids:
            return []
        now = status_changed_at or datetime.now(tzutc())

        async def _transit(_db_conn: SAConnection) -> list[tuple[SessionRow, bool]]:
            result: list[tuple[SessionRow, bool]] = []
            for sid in session_ids:
                row, is_transited = await self._transit_session_status(_db_conn, sid, now)
                result.append((row, is_transited))
            return result

        async with self.db.connect() as db_conn:
            result = await _transit(db_conn)
        for session_row, is_transited in result:
            if is_transited:
                await self._post_status_transition(session_row)
        return result

    async def register_status_updatable_session(self, session_ids: Iterable[SessionId]) -> None:
        if not session_ids:
            return

        try:
            await self.valkey_stat.register_session_ids_for_status_update(
                self.status_set_key,
                [self._encoder(sid) for sid in session_ids],
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to update session status to redis, skip. (e:{e!r})")

    async def get_status_updatable_sessions(self) -> set[SessionId]:
        try:
            results = await self.valkey_stat.get_and_clear_session_ids_for_status_update(
                self.status_set_key,
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to fetch session status data from redis, skip. (e:{e!r})")
            results = []
        result: list[SessionId] = []
        for raw_session_id in results:
            try:
                result.append(self._decoder(raw_session_id))
            except (ValueError, SyntaxError):
                log.warning(f"Cannot parse session id, skip. (id:{raw_session_id!r})")
                continue

        async with self.db.begin_readonly_session() as db_session:
            session_query = sa.select(SessionRow).where(
                SessionRow.status.in_(SessionStatus.kernel_awaiting_statuses())
            )
            session_rows = await db_session.scalars(session_query)
            session_ids = [row.id for row in session_rows]
        return {*result, *session_ids}

    async def deregister_status_updatable_session(
        self,
        session_ids: Iterable[SessionId],
    ) -> int:
        if not session_ids:
            return 0

        try:
            ret = await self.valkey_stat.remove_session_ids_from_status_update(
                self.status_set_key,
                [self._encoder(sid) for sid in session_ids],
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to remove session status data from redis, skip. (e:{e!r})")
            return 0
        return ret
