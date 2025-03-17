import asyncio
import functools
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Mapping, Optional, Protocol

import aiotools
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.validators import TimeDelta
from ai.backend.logging import BraceStyleAdapter

from ..api.context import RootContext
from ..config import session_hang_tolerance_iv
from ..models import SessionRow, UserRole
from ..models.session import SessionStatus
from ..models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionDestroyer(Protocol):
    async def destroy_session(
        self,
        session: SessionRow,
        *,
        forced: bool = False,
        reason: Optional[KernelLifecycleEventReason] = None,
        user_role: UserRole | None = None,
    ) -> Mapping[str, Any]: ...


def _get_interval(
    threshold: TimeDelta,
    *,
    max_interval: float = timedelta(hours=1).total_seconds(),
    heuristic_interval_weight: float = 0.4,  # NOTE: to repeat more than twice within the same time window.
) -> float:
    if isinstance(threshold, relativedelta):  # months, years
        return max_interval
    return min(max_interval, threshold.total_seconds() * heuristic_interval_weight)


async def handle_stale_sessions(
    db: ExtendedAsyncSAEngine,
    lifecycle_manager: SessionDestroyer,
    status: SessionStatus,
    threshold: TimeDelta,
    interval: float = 0,  # NOTE: `aiotools.create_timer()` passes `interval` to its `cb`.
) -> None:
    now = datetime.now(tz=tzutc())
    query = (
        sa.select(SessionRow)
        .where(SessionRow.status == status)
        .where(SessionRow.get_status_elapsed_time(status, now).total_seconds() > threshold.seconds)
        .options(
            noload("*"),
            load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
        )
    )

    async with db.begin_readonly() as conn:
        result = await conn.execute(query)
        sessions = result.fetchall()

    results_and_exceptions = await asyncio.gather(
        *[
            asyncio.create_task(
                lifecycle_manager.destroy_session(
                    session, forced=True, reason=KernelLifecycleEventReason.HANG_TIMEOUT
                ),
            )
            for session in sessions
        ],
        return_exceptions=True,
    )
    for result_or_exception in results_and_exceptions:
        if isinstance(result_or_exception, (BaseException, Exception)):
            log.error(
                "hanging session force-termination error: {}",
                repr(result_or_exception),
                exc_info=result_or_exception,
            )


@actxmgr
async def stale_session_collection_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    session_hang_tolerance = session_hang_tolerance_iv.check(
        await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
    )
    tasks: list[asyncio.Task] = []
    threshold: TimeDelta
    for raw_status, threshold in session_hang_tolerance["threshold"].items():
        try:
            status = SessionStatus[raw_status]
        except ValueError:
            log.warning(f"Invalid session status for hang-threshold: '{raw_status}'")
            continue

        interval = _get_interval(threshold)
        tasks.append(
            aiotools.create_timer(
                functools.partial(
                    handle_stale_sessions,
                    root_ctx.db,
                    root_ctx.registry,
                    status,
                    threshold,
                ),
                interval,
            ),
        )

    yield

    for task in tasks:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
