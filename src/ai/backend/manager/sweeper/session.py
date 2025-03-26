import asyncio
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator, override

import aiotools
import sqlalchemy as sa
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

if TYPE_CHECKING:
    from ..models.utils import ExtendedAsyncSAEngine
    from ..registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_SESSION_SWEEP_INTERVAL_SEC = 60.0


class SessionSweeper(AbstractSweeper):
    _status: SessionStatus
    _threshold: TimeDelta

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        *,
        status: SessionStatus,
        threshold: TimeDelta,
    ) -> None:
        super().__init__(db, registry)
        self._status = status
        self._threshold = threshold

    @override
    async def sweep(self) -> None:
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

        async with self._db.begin_readonly() as conn:
            result = await conn.execute(query)
            sessions = result.fetchall()

        await asyncio.gather(
            *[
                asyncio.create_task(
                    self._registry.destroy_session(
                        session, forced=True, reason=KernelLifecycleEventReason.HANG_TIMEOUT
                    ),
                )
                for session in sessions
            ],
            return_exceptions=False,
        )


@actxmgr
async def session_sweeper_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
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

        async def _sweep(interval: float) -> None:
            await SessionSweeper(
                root_ctx.db, root_ctx.registry, status=status, threshold=threshold
            ).sweep()

        tasks.append(aiotools.create_timer(_sweep, interval=DEFAULT_SESSION_SWEEP_INTERVAL_SEC))

    yield

    for task in tasks:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
