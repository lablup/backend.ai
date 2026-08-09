from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError, KeypairResourcePolicyNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    async def get_by_user_id(self, user_id: UUID) -> KeyPairResourcePolicyData:
        """Retrieves the keypair resource policy assigned to a user's default keypair."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(KeyPairResourcePolicyRow)
                .join(
                    KeyPairRow,
                    KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
                )
                .where(KeyPairRow.user == user_id)
                .where(KeyPairRow.is_active.is_(True))
                .limit(1)
            )
            row = await db_sess.scalar(query)
            if row is None:
                raise KeypairResourcePolicyNotFound(
                    f"Keypair resource policy for user '{user_id}' not found."
                )
            return row.to_dataclass()
