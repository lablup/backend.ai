from __future__ import annotations

from typing import Optional

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError, KeypairResourcePolicyNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

keypair_resource_policy_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.DB_SOURCE, layer=LayerType.KEYPAIR_RESOURCE_POLICY_DB_SOURCE
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


class KeypairResourcePolicyDBSource:
    """Database source for KeyPair resource policy operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @keypair_resource_policy_db_source_resilience.apply()
    async def insert(self, creator: Creator[KeyPairResourcePolicyRow]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            creator_result = await execute_creator(db_sess, creator)
            db_row = creator_result.row
            return db_row.to_dataclass()

    @keypair_resource_policy_db_source_resilience.apply()
    async def update(self, updater: Updater[KeyPairResourcePolicyRow]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise KeypairResourcePolicyNotFound(
                    f"Keypair resource policy with name {updater.pk_value} not found."
                )
            return result.row.to_dataclass()

    @keypair_resource_policy_db_source_resilience.apply()
    async def delete(self, name: str) -> KeyPairResourcePolicyData:
        """Deletes a keypair resource policy by name."""
        async with self._db.begin_session() as db_sess:
            delete_stmt = (
                sa.delete(KeyPairResourcePolicyRow)
                .where(KeyPairResourcePolicyRow.name == name)
                .returning(KeyPairResourcePolicyRow)
            )
            query_stms = (
                sa.select(KeyPairResourcePolicyRow)
                .from_statement(delete_stmt)
                .execution_options(populate_existing=True)
            )
            row: Optional[KeyPairResourcePolicyRow] = await db_sess.scalar(query_stms)
            if row is None:
                raise KeypairResourcePolicyNotFound(
                    f"Keypair resource policy with name {name} not found."
                )
            await db_sess.delete(row)
            return row.to_dataclass()
