import abc
import asyncio
import functools
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncIterator

import aiotools
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.logging import BraceStyleAdapter

from .api.context import RootContext
from .config import session_hang_tolerance_iv
from .models import KernelRow, SessionRow
from .models.session import KernelStatus, SessionStatus
from .models.utils import ExtendedAsyncSAEngine
from .registry import SessionDestroyer

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractCleaner(abc.ABC):
    _db: ExtendedAsyncSAEngine
    _lifecycle_manager: SessionDestroyer

    def __init__(self, db: ExtendedAsyncSAEngine, lifecycle_manager: SessionDestroyer) -> None:
        self._db = db
        self._lifecycle_manager = lifecycle_manager

    @abc.abstractmethod
    async def clean(
        self,
        status: KernelStatus | SessionStatus,
        threshold: relativedelta | timedelta,
        interval: float = 0,  # NOTE: `aiotools.create_timer()` passes the interval as an argument to its `callback`.
    ) -> None:
        raise NotImplementedError


class SessionCleaner(AbstractCleaner):
    async def clean(
        self,
        status: StrEnum,
        threshold: relativedelta | timedelta,
        interval: float = 0,
    ) -> None:
        query = (
            sa.select(SessionRow)
            .where(SessionRow.status == status)
            .where(
                (
                    datetime.now(tz=tzutc())
                    - SessionRow.status_history[status.name].astext.cast(
                        sa.types.DateTime(timezone=True)
                    )
                )
                >= threshold
            )
            .options(
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
            )
        )
        async with self._db.begin_readonly() as conn:
            result = await conn.execute(query)
            sessions = result.fetchall()
        log.warning(f"sessions: {sessions} (type: {type(sessions)})")
        log.warning(f"[SessionCleaner] [{datetime.now()}] {len(sessions)} items")

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(
                    self._lifecycle_manager.destroy_session(
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


class KernelCleaner(AbstractCleaner):
    async def clean(
        self,
        status: StrEnum,
        threshold: relativedelta | timedelta,
        interval: float = 0,
    ) -> None:
        query = (
            sa.select(SessionRow)
            .join(KernelRow)
            .where(KernelRow.status == status)
            .where(
                datetime.now(tz=tzutc())
                - KernelRow.status_history[status.name].astext.cast(
                    sa.types.DateTime(timezone=True)
                )
                >= threshold
            )
            .where(KernelRow.session_id == SessionRow.id)
            .distinct(SessionRow.id)
            .options(
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
            )
        )

        try:
            async with self._db.begin_readonly() as conn:
                result = await conn.execute(query)
                sessions = result.fetchall()
            log.warning(f"[KernelCleaner] sessions = {sessions}")
            log.warning(f"[KernelCleaner] {len(sessions)} items")
        except Exception as e:
            log.error(e)

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(
                    self._lifecycle_manager.destroy_session(
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


def get_interval(
    threshold: relativedelta | timedelta,
    *,
    max_interval: float = timedelta(hours=1).total_seconds(),
    heuristic_interval_weight: float = 0.4,  # NOTE: to repeat more than twice within the same time window.
) -> float:
    if isinstance(threshold, relativedelta):  # months, years
        return max_interval
    return min(max_interval, threshold.total_seconds() * heuristic_interval_weight)


@actxmgr
async def stale_session_kernel_cleaner_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    log.warning("stale_session_kernel_cleaner_ctx")
    try:
        session_hang_tolerance = session_hang_tolerance_iv.check(
            await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
        )
    except Exception as e:
        log.error(e)
    # log.warning(f"session_hang_tolerance: {session_hang_tolerance}")

    stale_container_cleaner_tasks = []
    threshold: relativedelta | timedelta
    for status, threshold in session_hang_tolerance["threshold"].items():
        try:
            session_status = SessionStatus[status]
        except KeyError:
            log.warning(f"Invalid session status for hang-threshold: '{status}'")
            continue
        interval = get_interval(threshold)
        stale_container_cleaner_tasks.append(
            aiotools.create_timer(
                functools.partial(
                    SessionCleaner(root_ctx.db, root_ctx.registry).clean,
                    root_ctx.registry,
                    session_status,
                    threshold,
                ),
                interval,
            )
        )
    for status, threshold in session_hang_tolerance["threshold"].items():
        try:
            kernel_status = KernelStatus[status]
        except KeyError:
            log.warning(f"Invalid kernel status for hang-threshold: '{status}'")
            continue
        interval = get_interval(threshold)
        stale_container_cleaner_tasks.append(
            aiotools.create_timer(
                functools.partial(
                    KernelCleaner(root_ctx.db, root_ctx.registry).clean,
                    kernel_status,
                    threshold,
                ),
                interval,
            )
        )

    yield

    for task in stale_container_cleaner_tasks:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
