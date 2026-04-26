from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.creators import (
    AppConfigPolicyCreatorSpec,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.app_config_policy.updaters import (
    AppConfigPolicyUpdaterSpec,
)
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

__all__ = (
    "AppConfigPolicyCreatorSpec",
    "AppConfigPolicyDBSource",
    "AppConfigPolicyUpdaterSpec",
)

app_config_policy_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.DB_SOURCE,
                layer=LayerType.APP_CONFIG_POLICY_DB_SOURCE,
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


class AppConfigPolicyDBSource:
    """Database operations for `app_config_policies`.

    All public methods own their transaction boundary. Mutations go
    through the shared Creator / Updater / Purger helpers so the
    ``integrity_error_checks`` wired into the specs translate DB
    constraint violations into typed domain errors (see
    :mod:`ai.backend.manager.repositories.app_config_policy.creators`).
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @app_config_policy_db_source_resilience.apply()
    async def get(self, config_name: str) -> AppConfigPolicyData | None:
        """Look up a policy by its `config_name` (UNIQUE)."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigPolicyRow).where(AppConfigPolicyRow.config_name == config_name)
            )
            return row.to_data() if row is not None else None

    @app_config_policy_db_source_resilience.apply()
    async def get_by_id(self, id: uuid.UUID) -> AppConfigPolicyData | None:
        """Look up a policy by row id."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigPolicyRow).where(AppConfigPolicyRow.id == id)
            )
            return row.to_data() if row is not None else None

    @app_config_policy_db_source_resilience.apply()
    async def create(self, creator: Creator[AppConfigPolicyRow]) -> AppConfigPolicyData:
        """Insert a new policy via the shared Creator helper.

        Duplicate `config_name` surfaces as :class:`AppConfigPolicyConflict`
        via the spec's ``integrity_error_checks``.
        """
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    @app_config_policy_db_source_resilience.apply()
    async def resolve_pk_by_config_name(
        self,
        config_name: str,
    ) -> uuid.UUID | None:
        """Resolve a policy's `config_name` (UNIQUE) to the row's UUID
        ``id``. Returns ``None`` when no row matches — callers translate
        to a domain-appropriate response."""
        async with self._db.begin_readonly_session() as db_sess:
            pk: uuid.UUID | None = await db_sess.scalar(
                sa.select(AppConfigPolicyRow.id).where(
                    AppConfigPolicyRow.config_name == config_name
                )
            )
            return pk

    @app_config_policy_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigPolicyRow]) -> AppConfigPolicyData | None:
        """Apply a pre-built Updater. Returns ``None`` when the row
        vanished between PK resolution and write; the caller maps this
        to :class:`AppConfigPolicyNotFound`."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            return result.row.to_data() if result is not None else None

    @app_config_policy_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigPolicyRow]) -> bool:
        """Apply a pre-built Purger. The DB-side FK from
        `app_config_fragments.name` (NO ACTION) blocks the delete while
        fragments still reference this policy — the service layer is
        expected to reject earlier with a friendlier error. Returns
        ``True`` only when a row was actually removed."""
        async with self._db.begin_session() as db_sess:
            result = await execute_purger(db_sess, purger)
            return result is not None

    @app_config_policy_db_source_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        """Paginated search across all policies."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigPolicyRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigPolicyRow.to_data() for row in result.rows]
            return AppConfigPolicySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
