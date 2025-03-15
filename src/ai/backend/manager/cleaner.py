import abc
import asyncio
import functools
import logging
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from typing import AsyncIterator

import aiotools

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.logging import BraceStyleAdapter

from .api.context import RootContext
from .models import SessionRow  # , KernelRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class Cleaner(abc.ABC):
    @abc.abstractmethod
    def clean(self) -> None:
        raise NotImplementedError


class SessionCleaner(Cleaner):
    def clean(self) -> None:
        pass


class KernelCleaner(Cleaner):
    def clean(self) -> None:
        pass


@actxmgr
async def hanging_session_cleaner_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    # stale, stuck
    from contextlib import suppress
    from datetime import timedelta
    from typing import TYPE_CHECKING

    import sqlalchemy as sa
    from dateutil.relativedelta import relativedelta
    from dateutil.tz import tzutc
    from sqlalchemy.orm import load_only, noload

    from .config import session_hang_tolerance_iv
    from .models.session import SessionStatus

    if TYPE_CHECKING:
        from .models.utils import ExtendedAsyncSAEngine

    async def _fetch_hanging_sessions(
        db: ExtendedAsyncSAEngine,
        status: SessionStatus,
        threshold: relativedelta | timedelta,
    ) -> tuple[SessionRow, ...]:
        # session_set: set[SessionRow] = set()
        query = (
            sa.select(SessionRow)
            .where(SessionRow.status == status)
            # TODO: session = TERMINATED / kernel = PREPARING
            .where(
                (
                    datetime.now(tz=tzutc())
                    - SessionRow.status_history[status.name].astext.cast(  # TODO: dict -> list
                        sa.types.DateTime(timezone=True)
                    )
                )
                > threshold
            )
            .options(  # TODO: vs select(SessionRow.id)
                noload("*"),
                load_only(SessionRow.id, SessionRow.name, SessionRow.status, SessionRow.access_key),
            )
        )
        async with db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.fetchall()
        # kernel_query = (
        #     sa.select(KernelRow.session_id)
        #     .where(KernelRow.status == status)
        #     .where(
        #         (
        #             datetime.now(tz=tzutc())
        #             - KernelRow.status_history[status.name].astext.cast(
        #                 sa.types.DateTime(timezone=True)
        #             )
        #         )
        #         > threshold
        #     )
        #     .options(
        #         noload("*"),
        #         load_only(KernelRow.session_id),
        #     )
        # )
        # async with db.begin_readonly() as conn:
        #     kernel_result = await conn.execute(kernel_query)
        #     # return kernel_result.fetchall()
        #     kernels = kernel_result.fetchall()
        # return x
        # return session_set

    async def _force_terminate_hanging_sessions(
        status: SessionStatus,
        threshold: relativedelta | timedelta,
        interval: float,  # NOTE: `aiotools.create_timer()` passes the interval value to its callable.
    ) -> None:
        try:
            # TODO: session + kernel status for multi-container
            sessions = await _fetch_hanging_sessions(root_ctx.db, status, threshold)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error("fetching hanging sessions error: {}", repr(e), exc_info=e)
            return

        log.debug(f"{len(sessions)} {status.name} sessions found.")

        results_and_exceptions = await asyncio.gather(
            *[
                asyncio.create_task(
                    root_ctx.registry.destroy_session(
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

    session_hang_tolerance = session_hang_tolerance_iv.check(
        await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
    )

    session_force_termination_tasks = []
    heuristic_interval_weight = 0.4  # NOTE: Shorter than a half(0.5)
    max_interval = timedelta(hours=1).total_seconds()
    threshold: relativedelta | timedelta
    for status, threshold in session_hang_tolerance["threshold"].items():
        try:
            session_status = SessionStatus[status]
        except KeyError:
            continue
        if isinstance(threshold, relativedelta):  # years, months
            interval = max_interval
        else:  # timedelta
            interval = min(max_interval, threshold.total_seconds() * heuristic_interval_weight)
        session_force_termination_tasks.append(
            aiotools.create_timer(
                functools.partial(_force_terminate_hanging_sessions, session_status, threshold),
                interval,
            )
        )

    yield

    for task in session_force_termination_tasks:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
