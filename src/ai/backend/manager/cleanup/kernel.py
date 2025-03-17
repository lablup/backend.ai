import asyncio
import functools
import logging
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from typing import AsyncIterator, Any, Mapping, Protocol, Sequence

import aiotools
import sqlalchemy as sa
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter

from ..api.context import RootContext
from ..models import KernelRow, SessionRow, DEAD_SESSION_STATUSES, DEAD_KERNEL_STATUSES
from ..models.utils import ExtendedAsyncSAEngine

__all__ = ("stale_kernel_collection_ctx",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelDestroyer(Protocol):
    async def destroy_session_lowlevel(
        self,
        session_id: SessionId,
        kernels: Sequence[
            Mapping[str, Any]
        ],  # should have (id, agent, agent_addr, container_id) columns
        reason: KernelLifecycleEventReason = KernelLifecycleEventReason.FAILED_TO_START,
    ) -> None: ...


async def handle_stale_kernels(
    db: ExtendedAsyncSAEngine,
    lifecycle_manager: KernelDestroyer,
    interval: float = 0,  # NOTE: `aiotools.create_timer()` passes `interval` to its `cb`.
) -> None:
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

    async with db.begin_readonly() as conn:
        result = await conn.execute(query)
        kernels = result.fetchall()

    kernels_per_session = defaultdict(list)
    for kernel in kernels:
        kernels_per_session[kernel.session_id].append(kernel)

    results_and_exceptions = await asyncio.gather(
        *[
            asyncio.create_task(
                lifecycle_manager.destroy_session_lowlevel(
                    session_id,
                    [
                        {
                            "id": kernel.id,
                            "session_id": kernel.session_id,
                            "agent": kernel.agent,
                            "agent_addr": kernel.agent_addr,
                            "container_id": kernel.container_id,
                        }
                        for kernel in kernels_
                    ],
                    reason=KernelLifecycleEventReason.HANG_TIMEOUT,
                )
            )
            for session_id, kernels_ in kernels_per_session.items()
        ],
        return_exceptions=True,
    )
    for result_or_exception in results_and_exceptions:
        if isinstance(result_or_exception, (BaseException, Exception)):
            log.error(
                "hanging kernel force-termination error: {}",
                repr(result_or_exception),
                exc_info=result_or_exception,
            )


@actxmgr
async def stale_kernel_collection_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    task = aiotools.create_timer(
        functools.partial(
            handle_stale_kernels,
            root_ctx.db,
            root_ctx.registry,
        ),
        interval=30,
    )

    yield

    if not task.done:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
