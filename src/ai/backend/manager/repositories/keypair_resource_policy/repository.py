from typing import Any, Mapping

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

keypair_resource_policy_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.KEYPAIR_RESOURCE_POLICY_REPOSITORY
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class KeypairResourcePolicyRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @keypair_resource_policy_repository_resilience.apply()
    async def create(self, fields: Mapping[str, Any]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            db_row = KeyPairResourcePolicyRow(**fields)
            db_sess.add(db_row)
            await db_sess.flush()
            # Refresh the object to ensure all attributes are loaded
            await db_sess.refresh(db_row)
            return db_row.to_dataclass()

    @keypair_resource_policy_repository_resilience.apply()
    async def get_by_name(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            return row.to_dataclass()

    @keypair_resource_policy_repository_resilience.apply()
    async def update(self, name: str, fields: Mapping[str, Any]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            for key, value in fields.items():
                setattr(row, key, value)
            await db_sess.flush()
            return row.to_dataclass()

    @keypair_resource_policy_repository_resilience.apply()
    async def delete(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            await db_sess.delete(row)
            return row.to_dataclass()
