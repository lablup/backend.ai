from __future__ import annotations

from uuid import UUID

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
    """The one read the generic ops cannot answer.

    Resolving a user's policy joins through ``keypairs`` and filters on the keypair
    being active, which the single-table lookup spec rules out.
    """

    _db_source: KeypairResourcePolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = KeypairResourcePolicyDBSource(db)

    @keypair_resource_policy_repository_resilience.apply()
    async def get_by_user_id(self, user_id: UUID) -> KeyPairResourcePolicyData:
        return await self._db_source.get_by_user_id(user_id)
