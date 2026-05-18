"""Admin-only repository for deployment queries that span every scope.

Holds reads that are not bounded by a project / user / domain scope. The
regular ``DeploymentRepository`` keeps the scoped variants; admin-style
"see everything" queries live here so the layering is explicit and the
GraphQL/REST ``admin_*`` paths have a clearly-named home.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.deployment.types import ModelDeploymentDataSearchResult
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.deployment.db_source.db_source import DeploymentDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("DeploymentAdminRepository",)


deployment_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.DEPLOYMENT_ADMIN_REPOSITORY,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class DeploymentAdminRepository:
    """Admin (no-scope) reads against the ``endpoints`` table.

    Holds its own ``DeploymentDBSource`` bound to the shared engine — the
    DBSource is a stateless query namespace, so every repository in the
    deployment package instantiates its own. The split exists so the
    calling layer makes its admin intent explicit; SQL-level helpers
    (e.g. ``_endpoint_row_to_deployment_data``) stay in ``db_source/``
    and are reused via that single module.
    """

    _db_source: DeploymentDBSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db_source = DeploymentDBSource(db)

    @deployment_admin_repository_resilience.apply()
    async def admin_search_deployments(
        self,
        querier: BatchQuerier,
    ) -> ModelDeploymentDataSearchResult:
        """Search every deployment without a scope filter.

        Callers may still pass arbitrary ``conditions`` through the
        querier — the absence of a scope filter on the repository method
        itself is what makes this admin-only. The ``admin_`` prefix is
        kept at every layer of the stack (db_source → repository →
        service → processor) so the unscoped intent is obvious at every
        call site, even when the class name (``DeploymentAdminRepository``)
        already telegraphs it.
        """
        return await self._db_source.admin_search_deployments(querier)
