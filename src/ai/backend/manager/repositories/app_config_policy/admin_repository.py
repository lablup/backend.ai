from __future__ import annotations

from collections.abc import Sequence

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
from ai.backend.manager.repositories.base.querier import BatchQuerier

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

    Mutations are routed through shared Creator / Updater / Purger
    helpers so DB constraint violations surface as typed domain errors
    (e.g., :class:`AppConfigPolicyConflict`).
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

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
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        """Update a policy. Raises ``AppConfigPolicyNotFound`` when missing."""
        spec = AppConfigPolicyUpdaterSpec(scope_sources=scope_sources)
        return await self._db_source.update(config_name, spec)

    @app_config_policy_admin_repository_resilience.apply()
    async def purge(self, config_name: str) -> bool:
        return await self._db_source.purge(config_name)

    @app_config_policy_admin_repository_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        return await self._db_source.search(querier)
