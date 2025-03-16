import asyncio
import functools
import logging
from contextlib import asynccontextmanager as actxmgr
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Mapping, Optional, Protocol, Union

import aiotools
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
from sqlalchemy import and_, or_
from sqlalchemy.orm import load_only, noload

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.validators import TimeDelta
from ai.backend.logging import BraceStyleAdapter

from .api.context import RootContext
from .config import session_hang_tolerance_iv
from .models import KernelRow, SessionRow, UserRole
from .models.session import KernelStatus, SessionStatus
from .models.utils import ExtendedAsyncSAEngine

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


def get_interval(
    threshold: TimeDelta,
    *,
    max_interval: float = timedelta(hours=1).total_seconds(),
    heuristic_interval_weight: float = 0.4,  # NOTE: to repeat more than twice within the same time window.
) -> float:
    if isinstance(threshold, relativedelta):  # months, years
        return max_interval
    return min(max_interval, threshold.total_seconds() * heuristic_interval_weight)


async def terminate_hanging_session_kernels(
    db: ExtendedAsyncSAEngine,
    lifecycle_manager: SessionDestroyer,
    status: SessionStatus | KernelStatus,
    threshold: TimeDelta,
    interval: float = 0,  # NOTE: `aiotools.create_timer()` passes `interval` to its `cb`.
):
    now = datetime.now(tz=tzutc())
    query = (
        sa.select(SessionRow)
        .join(KernelRow, KernelRow.session_id == SessionRow.id)
        .where(
            or_(
                # Condition for session-level
                and_(
                    SessionRow.status == status,
                    (
                        now
                        - SessionRow.status_history[status.name].astext.cast(
                            sa.types.DateTime(timezone=True)
                        )
                        >= threshold
                    ),
                ),
                # Condition for kernel-level
                and_(
                    KernelRow.status == status,
                    (
                        now
                        - KernelRow.status_history[status.name].astext.cast(
                            sa.types.DateTime(timezone=True)
                        )
                        >= threshold
                    ),
                ),
            )
        )
        .distinct(SessionRow.id)
        .options(
            noload("*"),
            load_only(SessionRow.id, SessionRow.name, SessionRow.access_key),
        )
    )

    try:
        async with db.begin_readonly() as conn:
            result = await conn.execute(query)
            sessions = result.fetchall()
    except Exception as e:
        log.error(e)
        raise e

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
async def hanging_session_scanner_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    try:
        session_hang_tolerance = session_hang_tolerance_iv.check(
            await root_ctx.shared_config.etcd.get_prefix_dict("config/session/hang-tolerance")
        )
    except Exception as e:
        log.error(e)
        raise e

    stale_container_cleaner_tasks = []
    threshold: TimeDelta

    def _validate_session_kernel_status(
        status: str,
    ) -> Optional[Union[SessionStatus, KernelStatus]]:
        for status_cls in {SessionStatus, KernelStatus}:
            try:
                return status_cls[status]  # type: ignore
            except ValueError:
                pass
        return None

    for raw_status, threshold in session_hang_tolerance["threshold"].items():
        if not (status := _validate_session_kernel_status(raw_status)):
            log.warning(f"Invalid session or kernel status for hang-threshold: '{status}'")
            continue

        interval = get_interval(threshold)
        stale_container_cleaner_tasks.append(
            aiotools.create_timer(
                functools.partial(
                    terminate_hanging_session_kernels,
                    root_ctx.db,
                    root_ctx.registry,
                    status,
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
