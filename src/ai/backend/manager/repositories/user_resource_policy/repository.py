from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user_resource_policy.db_source.db_source import (
    UserResourcePolicyDBSource,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

user_resource_policy_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.USER_RESOURCE_POLICY_REPOSITORY
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


class UserResourcePolicyRepository:
    """Repository for user resource policy data access."""

    _db_source: UserResourcePolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = UserResourcePolicyDBSource(db)

    @user_resource_policy_repository_resilience.apply()
    async def create(self, creator: Creator[UserResourcePolicyRow]) -> UserResourcePolicyData:
        """Creates a new user resource policy."""
        return await self._db_source.create(creator)

    @user_resource_policy_repository_resilience.apply()
    async def get_by_name(self, name: str) -> UserResourcePolicyData:
        """Retrieves a user resource policy by name."""
        return await self._db_source.get_by_name(name)

    @user_resource_policy_repository_resilience.apply()
    async def update(self, updater: Updater[UserResourcePolicyRow]) -> UserResourcePolicyData:
        """Updates an existing user resource policy."""
        return await self._db_source.update(updater)

    @user_resource_policy_repository_resilience.apply()
    async def delete(self, name: str) -> UserResourcePolicyData:
        """Deletes a user resource policy."""
        return await self._db_source.delete(name)
