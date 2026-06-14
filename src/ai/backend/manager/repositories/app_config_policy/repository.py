from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.types import SearchScope
from ai.backend.manager.repositories.ops import DBOpsProvider

app_config_policy_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_POLICY_REPOSITORY,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AppConfigPolicyRepository:
    """Non-admin repository for AppConfigPolicy.

    Holds operations available to any authenticated user (single-policy
    lookup and scoped search). Admin-only operations (create / update /
    purge / admin search) live on `AppConfigPolicyAdminRepository`.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigPolicyDBSource(ops_provider)

    @app_config_policy_repository_resilience.apply()
    async def get_by_id(self, id: AppConfigPolicyID) -> AppConfigPolicyData:
        return await self._db_source.get_by_id(id)

    @app_config_policy_repository_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AppConfigPolicySearchResult:
        return await self._db_source.scoped_search(querier, scopes)
