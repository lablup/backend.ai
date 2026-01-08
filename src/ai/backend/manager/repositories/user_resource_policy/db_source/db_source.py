from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError, UserResourcePolicyNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

user_resource_policy_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.USER_RESOURCE_POLICY_DB_SOURCE)
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


class UserResourcePolicyDBSource:
    """
    Database source for user resource policy operations.
    Handles all database operations for user resource policies.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @user_resource_policy_db_source_resilience.apply()
    async def create(self, creator: Creator[UserResourcePolicyRow]) -> UserResourcePolicyData:
        """Creates a new user resource policy."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_dataclass()

    @user_resource_policy_db_source_resilience.apply()
    async def get_by_name(self, name: str) -> UserResourcePolicyData:
        """Retrieves a user resource policy by name."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            row = await db_sess.scalar(query)
            if row is None:
                raise UserResourcePolicyNotFound(
                    f"User resource policy with name {name} not found."
                )
            return row.to_dataclass()

    @user_resource_policy_db_source_resilience.apply()
    async def update(self, updater: Updater[UserResourcePolicyRow]) -> UserResourcePolicyData:
        """Updates an existing user resource policy."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise UserResourcePolicyNotFound(
                    f"User resource policy with name {updater.pk_value} not found."
                )
            return result.row.to_dataclass()

    @user_resource_policy_db_source_resilience.apply()
    async def delete(self, name: str) -> UserResourcePolicyData:
        """Deletes a user resource policy."""
        async with self._db.begin_session() as db_sess:
            delete_stmt = (
                sa.delete(UserResourcePolicyRow)
                .where(UserResourcePolicyRow.name == name)
                .returning(UserResourcePolicyRow)
            )
            query_stms = (
                sa.select(UserResourcePolicyRow)
                .from_statement(delete_stmt)
                .execution_options(populate_existing=True)
            )
            row: Optional[UserResourcePolicyRow] = await db_sess.scalar(query_stms)
            if row is None:
                raise UserResourcePolicyNotFound(
                    f"User resource policy with name {name} not found."
                )
            await db_sess.delete(row)
            return row.to_dataclass()
