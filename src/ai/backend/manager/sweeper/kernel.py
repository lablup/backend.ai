import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from typing import AsyncIterator, Iterable, override

import aiotools
import sqlalchemy as sa
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus

from ..api.context import RootContext
from ..models import (
    DEAD_KERNEL_STATUSES,
    DEAD_SESSION_STATUSES,
    KernelRow,
    SessionRow,
)
from .base import DEFAULT_SWEEP_INTERVAL_SEC, AbstractSweeper

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelSweeper(AbstractSweeper):
    @override
    async def sweep(self) -> None:
        query = (
            sa.select(KernelRow)
            .join(SessionRow, KernelRow.session_id == SessionRow.id)
            .where(KernelRow.status.not_in({*DEAD_KERNEL_STATUSES, KernelStatus.ERROR}))
            .where(SessionRow.status.in_(DEAD_SESSION_STATUSES))
            .options(
                noload("*"),
                load_only(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.agent,
                    KernelRow.agent_addr,
                    KernelRow.container_id,
                ),
            )
        )

        async with self._db.begin_readonly() as conn:
            result = await conn.execute(query)
            kernels = result.fetchall()

        kernels_per_session = defaultdict(list)
        for kernel in kernels:
            kernels_per_session[kernel.session_id].append(kernel)

        async def _destroy_kernels(session_id: SessionId, kernels: Iterable[KernelRow]) -> None:
            try:
                await self._registry.destroy_session_lowlevel(
                    session_id,
                    [
                        {
                            "id": kernel.id,
                            "session_id": kernel.session_id,
                            "agent": kernel.agent,
                            "agent_addr": kernel.agent_addr,
                            "container_id": kernel.container_id,
                        }
                        for kernel in kernels
                    ],
                    reason=KernelLifecycleEventReason.HANG_TIMEOUT,
                )
            except Exception as e:
                self._sweeper_metric.observe_kernel_sweep(success=False)
                log.error("sweep(kernel) - failed to terminate kernels (s:{}).", session_id)
                raise e
            self._sweeper_metric.observe_kernel_sweep(success=True)
            log.info("sweep(kernel) - succeeded to terminate kernels (s:{}).", session_id)

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(_destroy_kernels(session_id, session_kernels))
                for session_id, session_kernels in kernels_per_session.items()
            ],
            return_exceptions=True,
        )
        results = [
            result_or_exception
            for result_or_exception in results_and_exceptions
            if not isinstance(result_or_exception, (BaseException, Exception))
        ]

        if kernels:
            log.info(
                "sweep(kernel) - {} orphan kernel(s) found, {} kernel(s) sweeped.",
                len(kernels),
                len(results),
            )
        else:
            log.debug("sweep(kernel) - No orphan kernels found.")


@actxmgr
async def stale_kernel_sweeper_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    async def _sweep(interval: float) -> None:
        await KernelSweeper(root_ctx.db, root_ctx.registry, root_ctx.metrics.sweeper).sweep()

    task = aiotools.create_timer(_sweep, interval=DEFAULT_SWEEP_INTERVAL_SEC)

    yield

    if not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
