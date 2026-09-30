"""Kernel reads and orderings only the v1 paths use.

Delete this file together with gql_legacy. `get_kernel` returns a row rather than
`KernelInfo` because the caller's cleanup callbacks take a row
(`event_dispatcher/handlers/stream_cleanup.py`); the v2 path reads kernels through
`KernelSearcher` and orders through `KernelSearchableFields.own.<field>.order`.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import noload, selectinload

from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel.statuses import DEAD_KERNEL_STATUSES
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry

__all__ = (
    "DEFAULT_KERNEL_ORDERING",
    "get_kernel",
)

DEFAULT_KERNEL_ORDERING = [
    sa.desc(
        sa.func.greatest(
            KernelRow.created_at,
            KernelRow.terminated_at,
            KernelRow.status_changed,
        )
    ),
]


async def get_kernel(
    db: ExtendedAsyncSAEngine, kern_id: uuid.UUID, allow_stale: bool = False
) -> KernelRow:
    async def _query() -> KernelRow:
        async with db.begin_readonly_session() as db_sess:
            query = (
                sa.select(KernelRow)
                .where(KernelRow.id == kern_id)
                .options(
                    noload("*"),
                    selectinload(KernelRow.agent_row).options(noload("*")),
                )
            )
            result = (await db_sess.execute(query)).scalars().all()

            cand = result
            if not allow_stale:
                cand = [
                    k
                    for k in result
                    if (k.status not in DEAD_KERNEL_STATUSES)
                    and (k.agent_row is not None and k.agent_row.status == AgentStatus.ALIVE)
                ]
            if not cand:
                raise SessionNotFound
            return cand[0]

    return await execute_with_retry(_query)
