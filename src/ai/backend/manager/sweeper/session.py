import asyncio
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime, timedelta
from typing import AsyncIterator, override

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
from ..models import SessionRow
from ..models.session import SessionStatus
from .base import AbstractSweeper

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionSweeper(AbstractSweeper):
    _root_ctx: RootContext
    _status: SessionStatus
    _threshold: TimeDelta

    def __init__(self, root_ctx: RootContext, status: SessionStatus, threshold: TimeDelta) -> None:
        self._root_ctx = root_ctx
        self._status = status
        self._threshold = threshold

    @override
    async def sweep(self, *args) -> None:
        now = datetime.now(tz=tzutc())
        query = (
            sa.select(SessionRow)
            .where(SessionRow.status == self._status)
            .where(SessionRow.get_status_elapsed_time(self._status, now) > self._threshold)
            .options(
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
            )
        )

        async with self._root_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            sessions = result.fetchall()

        await asyncio.gather(
            *[
                asyncio.create_task(
                    self._root_ctx.registry.destroy_session(
                        session, forced=True, reason=KernelLifecycleEventReason.HANG_TIMEOUT
                    ),
                )
                for session in sessions
            ],
            return_exceptions=False,
        )


def _get_interval(
    threshold: TimeDelta,
    *,
    max_interval: float = timedelta(hours=1).total_seconds(),
    heuristic_interval_weight: float = 0.4,  # NOTE: to repeat more than twice within the same time window.
) -> float:
    if isinstance(threshold, relativedelta):  # months, years
        return max_interval
    return min(max_interval, threshold.total_seconds() * heuristic_interval_weight)


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
                SessionSweeper(root_ctx, status, threshold).sweep,
                interval,
            ),
        )

    yield

    for task in tasks:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
