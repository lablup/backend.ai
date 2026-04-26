from __future__ import annotations

import uuid

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)

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
    """Read-side repository for AppConfigPolicy.

    Any authenticated user may read a policy — admin operations
    (create / update / purge / search) live on
    `AppConfigPolicyAdminRepository`.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

    @app_config_policy_repository_resilience.apply()
    async def get(self, config_name: str) -> AppConfigPolicyData | None:
        return await self._db_source.get(config_name)

    @app_config_policy_repository_resilience.apply()
    async def get_by_id(self, id: uuid.UUID) -> AppConfigPolicyData | None:
        return await self._db_source.get_by_id(id)
