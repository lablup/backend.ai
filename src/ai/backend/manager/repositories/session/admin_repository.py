from typing import Optional

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import SessionId
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.session import (
    KernelLoadingStrategy,
    SessionRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

session_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SESSION_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AdminSessionRepository:
    """
    Repository for admin-specific session operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @session_repository_resilience.apply()
    async def get_session_force(
        self,
        session_id: SessionId,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
        eager_loading_op: Optional[list] = None,
    ) -> SessionRow:
        """Get session without ownership validation (superadmin only)"""
        async with self._db.begin_readonly_session() as db_sess:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            if eager_loading_op:
                for op in eager_loading_op:
                    query_stmt = query_stmt.options(op)

            session_row = await db_sess.scalar(query_stmt)
            if session_row is None:
                raise SessionNotFound(f"Session not found (id:{session_id})")

            return session_row

    @session_repository_resilience.apply()
    async def get_session_to_determine_status_force(
        self,
        session_id: SessionId,
    ) -> SessionRow:
        """Get session for status determination without ownership checks"""
        async with self._db.begin_readonly_session() as db_sess:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            session_row = await db_sess.scalar(query_stmt)
            if session_row is None:
                raise SessionNotFound(f"Session not found (id:{session_id})")
            return session_row
