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
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    UserResourcePolicyModifier,
)
from ai.backend.manager.services.user_resource_policy.types import UserResourcePolicyCreator

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

user_resource_policy_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.USER_RESOURCE_POLICY_REPOSITORY)
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
    async def create(self, creator: UserResourcePolicyCreator) -> UserResourcePolicyData:
        """Creates a new user resource policy."""
        async with self._db.begin_session() as db_sess:
            db_row = UserResourcePolicyRow.from_creator(creator)
            db_sess.add(db_row)
            await db_sess.flush()
            return db_row.to_dataclass()

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
    async def update(
        self, name: str, modifier: UserResourcePolicyModifier
    ) -> UserResourcePolicyData:
        """Updates an existing user resource policy."""
        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            row: Optional[UserResourcePolicyRow] = await db_sess.scalar(query)
            if row is None:
                raise UserResourcePolicyNotFound(
                    f"User resource policy with name {name} not found."
                )
            fields = modifier.fields_to_update()
            query = (
                sa.update(UserResourcePolicyRow)
                .where(UserResourcePolicyRow.name == name)
                .values(**fields)
            )
            await db_sess.execute(query)
            return row.to_dataclass()

    @user_resource_policy_db_source_resilience.apply()
    async def delete(self, name: str) -> UserResourcePolicyData:
        """Deletes a user resource policy."""
        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            row: Optional[UserResourcePolicyRow] = await db_sess.scalar(query)
            if row is None:
                raise UserResourcePolicyNotFound(
                    f"User resource policy with name {name} not found."
                )
            await db_sess.delete(row)
            return row.to_dataclass()
