from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.errors.app_config import AppConfigPolicyNotFound
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.app_config_policy.creators import (
    AppConfigPolicyCreatorSpec,
)
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.app_config_policy.updaters import (
    AppConfigPolicyUpdaterSpec,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider

app_config_policy_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_POLICY_ADMIN_REPOSITORY,
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


class AppConfigPolicyAdminRepository:
    """Admin-only operations on AppConfigPolicy.

    Mutations (`create` / `update` / `purge`) and cross-policy
    `search` live here — read-side single lookups are on
    `AppConfigPolicyRepository`. Authorization is enforced at the
    service layer before reaching either repository.

    Update keeps `config_name` immutable; the FK on
    `app_config_fragments.name` is the defense-in-depth backstop for
    purge.

    Mutations are routed through the shared Creator / Updater / Purger
    helpers so DB constraint violations surface as typed domain errors
    (e.g., :class:`AppConfigPolicyConflict`).
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigPolicyDBSource(ops_provider)

    @app_config_policy_admin_repository_resilience.apply()
    async def create(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        creator: Creator[AppConfigPolicyRow] = Creator(
            spec=AppConfigPolicyCreatorSpec(
                config_name=config_name,
                scope_sources=scope_sources,
            ),
        )
        return await self._db_source.create(creator)

    @app_config_policy_admin_repository_resilience.apply()
    async def update(
        self,
        id: uuid.UUID,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        """Update a policy by id. Raises :class:`AppConfigPolicyNotFound`
        when the row is missing."""
        updater: Updater[AppConfigPolicyRow] = Updater(
            spec=AppConfigPolicyUpdaterSpec(scope_sources=scope_sources),
            pk_value=id,
        )
        result = await self._db_source.update(updater)
        if result is None:
            raise AppConfigPolicyNotFound(extra_msg=f"id={id!s}")
        return result

    @app_config_policy_admin_repository_resilience.apply()
    async def purge(self, id: uuid.UUID) -> bool:
        """Delete a policy by id. Returns ``True`` only when a row was
        actually removed."""
        purger: Purger[AppConfigPolicyRow] = Purger(
            row_class=AppConfigPolicyRow,
            pk_value=id,
        )
        return await self._db_source.purge(purger)

    @app_config_policy_admin_repository_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        return await self._db_source.search(querier)
