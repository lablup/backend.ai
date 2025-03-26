import asyncio
import logging
import math
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from typing import AsyncIterator, override

import aiotools
import sqlalchemy as sa
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.validators import TimeDelta
from ai.backend.logging import BraceStyleAdapter

from ..api.context import RootContext
from ..config import session_hang_tolerance_iv
from ..models import DEAD_KERNEL_STATUSES, DEAD_SESSION_STATUSES, KernelRow, SessionRow
from .base import AbstractSweeper

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_KERNEL_SWEEP_INTERVAL_SEC = 60.0


class KernelSweeper(AbstractSweeper):
    @override
    async def sweep(self, *args) -> None:
        query = (
            sa.select(KernelRow)
            .join(SessionRow, KernelRow.session_id == SessionRow.id)
            .where(KernelRow.status.not_in(DEAD_KERNEL_STATUSES))
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

        await asyncio.gather(
            *[
                asyncio.create_task(
                    self._registry.destroy_session_lowlevel(
                        session_id,
                        [
                            {
                                "id": kernel.id,
                                "session_id": kernel.session_id,
                                "agent": kernel.agent,
                                "agent_addr": kernel.agent_addr,
                                "container_id": kernel.container_id,
                            }
                            for kernel in session_kernels
                        ],
                        reason=KernelLifecycleEventReason.HANG_TIMEOUT,
                    )
                )
                for session_id, session_kernels in kernels_per_session.items()
            ],
            return_exceptions=False,
        )


@actxmgr
async def stale_kernel_collection_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    session_hang_tolerance = session_hang_tolerance_iv.check(
        await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
    )
    interval_sec = math.inf
    threshold: TimeDelta
    for threshold in session_hang_tolerance["threshold"].values():
        interval_sec = min(interval_sec, threshold.seconds)
    if interval_sec == math.inf:
        interval_sec = DEFAULT_KERNEL_SWEEP_INTERVAL_SEC
    task = aiotools.create_timer(
        KernelSweeper(db=root_ctx.db, registry=root_ctx.registry).sweep,
        interval=interval_sec,
    )

    yield

    if not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
