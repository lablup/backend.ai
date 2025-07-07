import logging
from io import BytesIO

import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.events.event_types.kernel.anycast import (
    DoSyncKernelLogsEvent,
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelHeartbeatEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
    KernelTerminatingAnycastEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.registry import AgentRegistry

from ...models.kernel import kernels
from ...models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelEventHandler:
    _valkey_stream: ValkeyStreamClient
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine

    def __init__(
        self, valkey_stream: ValkeyStreamClient, registry: AgentRegistry, db: ExtendedAsyncSAEngine
    ) -> None:
        self._valkey_stream = valkey_stream
        self._registry = registry
        self._db = db

    async def handle_kernel_log(
        self,
        context: None,
        source: AgentId,
        event: DoSyncKernelLogsEvent,
    ) -> None:
        # The log data is at most 10 MiB.
        log_buffer = BytesIO()
        try:
            list_size = await self._valkey_stream.container_log_len(container_id=event.container_id)
            if list_size is None:
                # The log data is expired due to a very slow event delivery.
                # (should never happen!)
                log.warning(
                    "tried to store console logs for cid:{}, but the data is expired",
                    event.container_id,
                )
                return
            for _ in range(list_size):
                # Read chunk-by-chunk to allow interleaving with other Redis operations.
                chunks = await self._valkey_stream.pop_container_logs(
                    container_id=event.container_id
                )
                if chunks is None:  # maybe missing
                    log_buffer.write(b"(container log unavailable)\n")
                    break
                for chunk in chunks:
                    log_buffer.write(chunk)
            try:
                log_data = log_buffer.getvalue()

                async def _update_log() -> None:
                    async with self._db.begin() as conn:
                        update_query = (
                            sa.update(kernels)
                            .values(container_log=log_data)
                            .where(kernels.c.id == event.kernel_id)
                        )
                        await conn.execute(update_query)

                await execute_with_retry(_update_log)
            finally:
                # Clear the log data from Redis when done.
                await self._valkey_stream.clear_container_logs(container_id=event.container_id)
        finally:
            log_buffer.close()

    async def handle_kernel_creation_lifecycle(
        self,
        context: None,
        source: AgentId,
        event: (
            KernelPreparingAnycastEvent
            | KernelPullingAnycastEvent
            | KernelCreatingAnycastEvent
            | KernelStartedAnycastEvent
            | KernelCancelledAnycastEvent
        ),
    ) -> None:
        """
        Update the database and perform post_create_kernel() upon
        the events for each step of kernel creation.

        To avoid race condition between consumer and subscriber event handlers,
        we only have this handler to subscribe all kernel creation events,
        but distinguish which one to process using a unique creation_id
        generated when initiating the create_kernels() agent RPC call.
        """
        log.debug(
            "handle_kernel_creation_lifecycle: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )
        match event:
            case KernelPreparingAnycastEvent():
                # State transition is done by the DoPrepareEvent handler inside the scheduler-distpacher object.
                pass
            case KernelPullingAnycastEvent(kernel_id, session_id, reason=reason):
                async with self._db.connect() as db_conn:
                    await self._registry.mark_kernel_pulling(db_conn, kernel_id, session_id, reason)
            case KernelCreatingAnycastEvent(kernel_id, session_id, reason=reason):
                async with self._db.connect() as db_conn:
                    await self._registry.mark_kernel_creating(
                        db_conn, kernel_id, session_id, reason
                    )
            case KernelStartedAnycastEvent(
                kernel_id, session_id, reason=reason, creation_info=creation_info
            ):
                async with self._db.connect() as db_conn:
                    await self._registry.mark_kernel_running(
                        db_conn, kernel_id, session_id, reason, creation_info
                    )
            case KernelCancelledAnycastEvent():
                log.warning(f"Kernel cancelled, {event.reason = }")

    async def handle_kernel_preparing(
        self,
        context: None,
        source: AgentId,
        event: KernelPreparingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_preparing: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )
        # State transition is done by the DoPrepareEvent handler inside the scheduler-distpacher object.

    async def handle_kernel_pulling(
        self,
        context: None,
        source: AgentId,
        event: KernelPullingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_pulling: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )
        async with self._db.connect() as db_conn:
            await self._registry.mark_kernel_pulling(
                db_conn, event.kernel_id, event.session_id, event.reason
            )

    async def handle_kernel_creating(
        self,
        context: None,
        source: AgentId,
        event: KernelCreatingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_creating: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )
        async with self._db.connect() as db_conn:
            await self._registry.mark_kernel_creating(
                db_conn, event.kernel_id, event.session_id, event.reason
            )

    async def handle_kernel_started(
        self,
        context: None,
        source: AgentId,
        event: KernelStartedAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_started: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )
        async with self._db.connect() as db_conn:
            await self._registry.mark_kernel_running(
                db_conn, event.kernel_id, event.session_id, event.reason, event.creation_info
            )

    async def handle_kernel_cancelled(
        self,
        context: None,
        source: AgentId,
        event: KernelCancelledAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_cancelled: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

    async def handle_kernel_terminating(
        self,
        context: None,
        source: AgentId,
        event: KernelTerminatingAnycastEvent,
    ) -> None:
        # `destroy_kernel()` has already changed the kernel status to "TERMINATING".
        pass

    async def handle_kernel_terminated(
        self,
        context: None,
        source: AgentId,
        event: KernelTerminatedAnycastEvent,
    ) -> None:
        async with self._db.connect() as db_conn:
            await self._registry.mark_kernel_terminated(
                db_conn, event.kernel_id, event.session_id, event.reason, event.exit_code
            )

    async def handle_kernel_heartbeat(
        self,
        context: None,
        source: AgentId,
        event: KernelHeartbeatEvent,
    ) -> None:
        await self._registry.mark_kernel_heartbeat(event.kernel_id)
