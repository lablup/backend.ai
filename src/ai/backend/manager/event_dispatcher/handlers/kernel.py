import logging
from io import BytesIO

import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.events.event_types.kernel.anycast import (
    DoSyncKernelLogsEvent,
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
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
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelEventHandler:
    _valkey_container_log: ValkeyContainerLogClient
    _valkey_stat: ValkeyStatClient
    _valkey_stream: ValkeyStreamClient
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _schedule_coordinator: ScheduleCoordinator

    def __init__(
        self,
        valkey_container_log: ValkeyContainerLogClient,
        valkey_stat: ValkeyStatClient,
        valkey_stream: ValkeyStreamClient,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        self._valkey_container_log = valkey_container_log
        self._valkey_stat = valkey_stat
        self._valkey_stream = valkey_stream
        self._registry = registry
        self._db = db
        self._schedule_coordinator = schedule_coordinator

    async def handle_kernel_log(
        self,
        _context: None,
        _source: AgentId,
        event: DoSyncKernelLogsEvent,
    ) -> None:
        # The log data is at most 10 MiB.
        log_buffer = BytesIO()
        try:
            list_size = await self._valkey_container_log.container_log_len(
                container_id=event.container_id
            )
            for _ in range(list_size):
                # Read chunk-by-chunk to allow interleaving with other Redis operations.
                chunks = await self._valkey_container_log.pop_container_logs(
                    container_id=event.container_id
                )
                if chunks is None:  # maybe missing
                    log_buffer.write(b"(container log unavailable)\n")
                    break
                for chunk in chunks:
                    log_buffer.write(chunk.get_content())
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
                await self._valkey_container_log.clear_container_logs(
                    container_id=event.container_id
                )
        except Exception:
            # skip all exception in handle_kernel_log
            pass
        finally:
            log_buffer.close()

    async def handle_kernel_preparing(
        self,
        _context: None,
        _source: AgentId,
        event: KernelPreparingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_preparing: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

        await self._schedule_coordinator.handle_kernel_preparing(event)

    async def handle_kernel_pulling(
        self,
        _context: None,
        _source: AgentId,
        event: KernelPullingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_pulling: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

        await self._schedule_coordinator.handle_kernel_pulling(event)

    async def handle_kernel_creating(
        self,
        _context: None,
        _source: AgentId,
        event: KernelCreatingAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_creating: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

        await self._schedule_coordinator.handle_kernel_creating(event)

    async def handle_kernel_started(
        self,
        _context: None,
        _source: AgentId,
        event: KernelStartedAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_started: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

        await self._schedule_coordinator.handle_kernel_running(event)

    async def handle_kernel_cancelled(
        self,
        _context: None,
        _source: AgentId,
        event: KernelCancelledAnycastEvent,
    ) -> None:
        log.info(
            "handle_kernel_cancelled: ev:{} k:{}",
            event.event_name(),
            event.kernel_id,
        )

        await self._schedule_coordinator.handle_kernel_cancelled(event)

    async def handle_kernel_terminating(
        self,
        context: None,
        source: AgentId,
        event: KernelTerminatingAnycastEvent,
    ) -> None:
        # `destroy_kernel()` has already changed the kernel status to "TERMINATING".
        # No additional handling needed for terminating state
        pass

    async def handle_kernel_terminated(
        self,
        _context: None,
        _source: AgentId,
        event: KernelTerminatedAnycastEvent,
    ) -> None:
        await self._schedule_coordinator.handle_kernel_terminated(event)
