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
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    KeyPairResourcePolicyModifier,
)
from ai.backend.manager.services.keypair_resource_policy.types import KeyPairResourcePolicyCreator

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
    async def insert(self, creator: KeyPairResourcePolicyCreator) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            db_row = KeyPairResourcePolicyRow.from_creator(creator)
            db_sess.add(db_row)
            await db_sess.flush()
            # Refresh the object to ensure all attributes are loaded
            await db_sess.refresh(db_row)
            return db_row.to_dataclass()

    @keypair_resource_policy_db_source_resilience.apply()
    async def update(
        self, name: str, modifier: KeyPairResourcePolicyModifier
    ) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            check_query = sa.select(KeyPairResourcePolicyRow).where(
                KeyPairResourcePolicyRow.name == name
            )
            existing_row = await db_sess.scalar(check_query)
            if existing_row is None:
                raise KeypairResourcePolicyNotFound(
                    f"Keypair resource policy with name {name} not found."
                )
            fields = modifier.fields_to_update()
            update_stmt = (
                sa.update(KeyPairResourcePolicyRow)
                .where(KeyPairResourcePolicyRow.name == name)
                .values(**fields)
                .returning(KeyPairResourcePolicyRow)
            )
            query_stmt = (
                sa.select(KeyPairResourcePolicyRow)
                .from_statement(update_stmt)
                .execution_options(populate_existing=True)
            )
            updated_row: Optional[KeyPairResourcePolicyRow] = await db_sess.scalar(query_stmt)
            if updated_row is None:
                raise KeypairResourcePolicyNotFound(
                    f"Keypair resource policy with name {name} not found after update."
                )
            return updated_row.to_dataclass()

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
