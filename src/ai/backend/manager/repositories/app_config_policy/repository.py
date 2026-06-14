from __future__ import annotations

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

    Holds operations available to any authenticated user (currently a
    single-policy lookup). Admin-only operations (create / update /
    purge / search) live on `AppConfigPolicyAdminRepository`.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigPolicyDBSource(ops_provider)

    @app_config_policy_repository_resilience.apply()
    async def get_by_id(self, id: AppConfigPolicyID) -> AppConfigPolicyData:
        return await self._db_source.get_by_id(id)
