import asyncio
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime
from typing import AsyncIterator, Mapping, override

import aiotools
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy import and_
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.metrics.metric import SweeperMetricObserver
from ai.backend.common.validators import TimeDelta
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus

from ..api.context import RootContext
from ..config_legacy import session_hang_tolerance_iv
from ..models import SessionRow
from ..models.utils import ExtendedAsyncSAEngine
from ..registry import AgentRegistry
from .base import DEFAULT_SWEEP_INTERVAL_SEC, AbstractSweeper

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionSweeper(AbstractSweeper):
    _status_threshold_map: Mapping[SessionStatus, TimeDelta]

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        sweeper_metric: SweeperMetricObserver,
        *,
        status_threshold_map: Mapping[SessionStatus, TimeDelta],
    ) -> None:
        super().__init__(db, registry, sweeper_metric)
        self._status_threshold_map = status_threshold_map

    @override
    async def sweep(self) -> None:
        now = datetime.now(tz=tzutc())

        for status, threshold in self._status_threshold_map.items():
            query = (
                sa.select(SessionRow)
                .where(
                    and_(
                        SessionRow.status == status,
                        SessionRow.get_status_elapsed_time(status, now) > threshold,
                    )
                )
                .options(
                    noload("*"),
                    load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
                )
            )

            async with self._db.begin_readonly() as conn:
                result = await conn.execute(query)
                sessions = result.fetchall()

            async def _destroy_session(session: SessionRow) -> None:
                try:
                    await self._registry.destroy_session(
                        session, forced=True, reason=KernelLifecycleEventReason.HANG_TIMEOUT
                    )
                except Exception as e:
                    self._sweeper_metric.observe_session_sweep(status=status, success=False)
                    log.error(
                        "sweep(session) - failed to terminate {} session (s:{}).",
                        status,
                        session.id,
                        exc_info=e,
                    )
                    raise e
                self._sweeper_metric.observe_session_sweep(status=status, success=True)
                log.info(
                    "sweep(session) - succeeded to terminate {} session (s:{}).",
                    status,
                    session.id,
                )

            results_and_exceptions = await asyncio.gather(
                *[asyncio.create_task(_destroy_session(session)) for session in sessions],
                return_exceptions=True,
            )
            results = [
                result_or_exception
                for result_or_exception in results_and_exceptions
                if not isinstance(result_or_exception, (BaseException, Exception))
            ]

            if sessions:
                log.info(
                    "sweep(session) - {} {} session(s) found, {} session(s) sweeped.",
                    len(sessions),
                    status,
                    len(results),
                )
            else:
                log.debug("sweep(session) - No {} sessions found.", status)


@actxmgr
async def stale_session_sweeper_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    # TODO: Resolve type issue and, Use `session_hang_tolerance` from the unified config
    session_hang_tolerance = session_hang_tolerance_iv.check(
        await root_ctx.etcd.get_prefix_dict("config/session/hang-tolerance")
    )
    status_threshold_map: dict[SessionStatus, TimeDelta] = {}
    for status, threshold in session_hang_tolerance["threshold"].items():
        try:
            status_threshold_map[SessionStatus(status)] = threshold
        except ValueError:
            log.warning("sweep(session) - Skipping invalid session status '{}'.", status)

    async def _sweep(interval: float) -> None:
        await SessionSweeper(
            root_ctx.db,
            root_ctx.registry,
            root_ctx.metrics.sweeper,
            status_threshold_map=status_threshold_map,
        ).sweep()

    task = aiotools.create_timer(_sweep, interval=DEFAULT_SWEEP_INTERVAL_SEC)

    yield

    if not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
