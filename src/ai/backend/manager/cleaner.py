import asyncio
import functools
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncIterator, Protocol

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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# class Cleaner(abc.ABC):
#     _root_ctx: RootContext

#     def __init__(self, root_ctx: RootContext) -> None:
#         self._root_ctx = root_ctx

#     @abc.abstractmethod
#     async def clean(
#         self,
#         status: StrEnum,
#         threshold: relativedelta | timedelta,
#         interval: float,  # NOTE: `aiotools.create_timer()` passes the interval value to its callable.
#     ) -> None:
#         raise NotImplementedError

# @abc.abstractmethod
# async def fetch(self, status: str, threshold: relativedelta | timedelta) -> Iterable:
#     raise NotImplementedError


class Cleaner(Protocol):
    async def clean(
        self,
        root_ctx: RootContext,
        status: KernelStatus | SessionStatus,
        threshold: relativedelta | timedelta,
        interval: float,
    ) -> None: ...


class SessionCleaner:
    async def clean(
        self, status: StrEnum, threshold: relativedelta | timedelta, interval: float
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
                > threshold
            )
            .options(
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
            )
        )
        async with self._root_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            sessions = result.fetchall()
        log.warning(f"[SessionCleaner] [{datetime.now()}] {len(sessions)} items")

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(
                    self._root_ctx.registry.destroy_session(
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


class KernelCleaner:
    async def clean(
        self, status: StrEnum, threshold: relativedelta | timedelta, interval: float
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
                > threshold
            )
            .where(KernelRow.session_id == SessionRow.id)
            .distinct(SessionRow.id)
            .options(
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
            )
        )

        try:
            async with self._root_ctx.db.begin_readonly() as conn:
                result = await conn.execute(query)
                sessions = result.fetchall()
            log.warning(f"[KernelCleaner] sessions = {sessions}")
            log.warning(f"[KernelCleaner] {len(sessions)} items")
        except Exception as e:
            log.error(e)

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(
                    self._root_ctx.registry.destroy_session(
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
    # xxx = await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
    # log.warning(f"xxxxxxxx = {xxx.items()}")
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
                    SessionCleaner(root_ctx).clean,
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
                    KernelCleaner(root_ctx).clean,
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
