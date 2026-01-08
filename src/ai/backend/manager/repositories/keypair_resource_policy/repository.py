from __future__ import annotations

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair_resource_policy.db_source.db_source import (
    KeypairResourcePolicyDBSource,
)

keypair_resource_policy_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.KEYPAIR_RESOURCE_POLICY_REPOSITORY
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


class KeypairResourcePolicyRepository:
    _db_source: KeypairResourcePolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = KeypairResourcePolicyDBSource(db)

    @keypair_resource_policy_repository_resilience.apply()
    async def create_keypair_resource_policy(
        self, creator: Creator[KeyPairResourcePolicyRow]
    ) -> KeyPairResourcePolicyData:
        return await self._db_source.insert(creator)

    @keypair_resource_policy_repository_resilience.apply()
    async def update_keypair_resource_policy(
        self, updater: Updater[KeyPairResourcePolicyRow]
    ) -> KeyPairResourcePolicyData:
        return await self._db_source.update(updater)

    @keypair_resource_policy_repository_resilience.apply()
    async def remove_keypair_resource_policy(self, name: str) -> KeyPairResourcePolicyData:
        return await self._db_source.delete(name)
