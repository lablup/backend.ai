from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Final

from ai.backend.common import validators as tx
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.idle import AppStreamingStatus, IdleCheckerHost
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.stream.repository import StreamRepository
from ai.backend.manager.services.stream.actions.execute_in_stream import (
    ExecuteInStreamAction,
    ExecuteInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.gc_stale_connections import (
    GCStaleConnectionsAction,
    GCStaleConnectionsActionResult,
)
from ai.backend.manager.services.stream.actions.get_streaming_session import (
    GetStreamingSessionAction,
    GetStreamingSessionActionResult,
)
from ai.backend.manager.services.stream.actions.interrupt_in_stream import (
    InterruptInStreamAction,
    InterruptInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.restart_in_stream import (
    RestartInStreamAction,
    RestartInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.start_service_in_stream import (
    StartServiceInStreamAction,
    StartServiceInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.track_connection import (
    TrackConnectionAction,
    TrackConnectionActionResult,
)
from ai.backend.manager.services.stream.actions.untrack_connection import (
    UntrackConnectionAction,
    UntrackConnectionActionResult,
)

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StreamService:
    _repository: StreamRepository
    _registry: AgentRegistry
    _valkey_live: ValkeyLiveClient
    _idle_checker_host: IdleCheckerHost
    _etcd: AsyncEtcd

    def __init__(
        self,
        repository: StreamRepository,
        registry: AgentRegistry,
        valkey_live: ValkeyLiveClient,
        idle_checker_host: IdleCheckerHost,
        etcd: AsyncEtcd,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._valkey_live = valkey_live
        self._idle_checker_host = idle_checker_host
        self._etcd = etcd

    async def get_streaming_session(
        self, action: GetStreamingSessionAction
    ) -> GetStreamingSessionActionResult:
        session = await self._repository.get_streaming_session(
            action.session_name, AccessKey(action.access_key)
        )
        kernel = session.main_kernel
        return GetStreamingSessionActionResult(
            session_id=str(session.id),
            kernel_id=str(kernel.id),
            kernel_host=kernel.kernel_host,
            agent_addr=kernel.agent_addr,
            repl_in_port=kernel.repl_in_port,
            repl_out_port=kernel.repl_out_port,
            service_ports=kernel.service_ports or [],
        )

    async def execute_in_stream(self, action: ExecuteInStreamAction) -> ExecuteInStreamActionResult:
        session = await self._repository.get_streaming_session(
            action.session_name, AccessKey(action.access_key)
        )
        result = await self._registry.execute(
            session,
            action.api_version,
            action.run_id,
            action.mode,
            action.code,
            action.opts,
            flush_timeout=action.flush_timeout,
        )
        return ExecuteInStreamActionResult(result=dict(result))

    async def restart_in_stream(self, action: RestartInStreamAction) -> RestartInStreamActionResult:
        session = await self._repository.get_streaming_session(
            action.session_name, AccessKey(action.access_key)
        )
        await self._registry.restart_session(session)
        return RestartInStreamActionResult()

    async def interrupt_in_stream(
        self, action: InterruptInStreamAction
    ) -> InterruptInStreamActionResult:
        session = await self._repository.get_streaming_session(
            action.session_name, AccessKey(action.access_key)
        )
        result = await self._registry.interrupt_session(session)
        return InterruptInStreamActionResult(result=dict(result))

    async def start_service_in_stream(
        self, action: StartServiceInStreamAction
    ) -> StartServiceInStreamActionResult:
        session = await self._repository.get_streaming_session(
            action.session_name, AccessKey(action.access_key)
        )
        result = await self._registry.start_service(session, action.service, action.opts)
        return StartServiceInStreamActionResult(result=dict(result))

    def create_connection_refresh_callback(
        self,
        kernel_id: KernelId,
        service: str,
        stream_id: str,
    ) -> Callable[..., Awaitable[None]]:
        async def update_connection_tracker() -> None:
            await self._valkey_live.update_app_connection_tracker(
                str(kernel_id), service, stream_id
            )

        return update_connection_tracker

    async def track_connection(self, action: TrackConnectionAction) -> TrackConnectionActionResult:
        await self._valkey_live.update_connection_tracker(
            str(action.kernel_id), action.service, action.stream_id
        )
        await self._idle_checker_host.update_app_streaming_status(
            action.session_id,
            AppStreamingStatus.HAS_ACTIVE_CONNECTIONS,
        )
        return TrackConnectionActionResult(kernel_id=str(action.kernel_id))

    async def untrack_connection(
        self, action: UntrackConnectionAction
    ) -> UntrackConnectionActionResult:
        await self._valkey_live.remove_connection_tracker(
            str(action.kernel_id), action.service, action.stream_id
        )
        remaining_count = await self._valkey_live.count_active_connections(str(action.kernel_id))
        if remaining_count == 0:
            await self._idle_checker_host.update_app_streaming_status(
                action.session_id,
                AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
            )
        return UntrackConnectionActionResult(
            kernel_id=str(action.kernel_id),
            remaining_count=remaining_count,
        )

    async def gc_stale_connections(
        self, action: GCStaleConnectionsAction
    ) -> GCStaleConnectionsActionResult:
        no_packet_timeout: timedelta = tx.TimeDuration().check(
            await self._etcd.get("config/idle/app-streaming-packet-timeout") or "5m",
        )
        now = await self._valkey_live.get_server_time()
        removed_sessions: list[str] = []
        for session_id in action.active_session_ids:
            prev_remaining = await self._valkey_live.count_active_connections(str(session_id))
            removed_count = await self._valkey_live.remove_stale_connections(
                str(session_id),
                now - no_packet_timeout.total_seconds(),
            )
            remaining = await self._valkey_live.count_active_connections(str(session_id))
            log.debug(
                "conn_tracker: gc {} removed/remaining = {}/{}",
                session_id,
                removed_count,
                remaining,
            )
            if prev_remaining > 0 and remaining == 0:
                await self._idle_checker_host.update_app_streaming_status(
                    SessionId(session_id),
                    AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
                )
                removed_sessions.append(str(session_id))
        return GCStaleConnectionsActionResult(removed_sessions=removed_sessions)
