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

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.validators import TimeDelta
from ai.backend.logging import BraceStyleAdapter

from ..api.context import RootContext
from ..config import session_hang_tolerance_iv
from ..models import SessionRow
from ..models.session import SessionStatus
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
        *,
        status_threshold_map: Mapping[SessionStatus, TimeDelta],
    ) -> None:
        super().__init__(db, registry)
        self._status_threshold_map = status_threshold_map

    @override
    async def sweep(self) -> None:
        now = datetime.now(tz=tzutc())

        for status, threshold in self._status_threshold_map.items():
            query = (
                sa.select(SessionRow)
                # .where(or_(*conditions))
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

            results_and_exceptions = await asyncio.gather(
                *[
                    asyncio.create_task(
                        self._registry.destroy_session(
                            session, forced=True, reason=KernelLifecycleEventReason.HANG_TIMEOUT
                        ),
                    )
                    for session in sessions
                ],
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
async def session_sweeper_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    session_hang_tolerance = session_hang_tolerance_iv.check(
        await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
    )

    async def _sweep(interval: float) -> None:
        await SessionSweeper(
            root_ctx.db,
            root_ctx.registry,
            status_threshold_map=session_hang_tolerance["threshold"],
        ).sweep()

    task = aiotools.create_timer(_sweep, interval=DEFAULT_SWEEP_INTERVAL_SEC)

    yield

    if not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
