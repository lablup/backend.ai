from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.vfolder.types import VFolderSearchResult
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("VFolderAdminRepository",)

vfolder_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.VFOLDER_ADMIN_REPOSITORY)
        ),
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


class VFolderAdminRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @vfolder_admin_repository_resilience.apply()
    async def search_vfolders(
        self,
        querier: BatchQuerier,
    ) -> VFolderSearchResult:
        """Search all vfolders with pagination and filters (admin, no scope).

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            VFolderSearchResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(VFolderRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.VFolderRow.to_data() for row in result.rows]

            return VFolderSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
