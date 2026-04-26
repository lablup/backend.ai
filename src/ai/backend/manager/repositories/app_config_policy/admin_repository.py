from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.errors.app_config import AppConfigPolicyNotFound
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
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater

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


def _missing(config_name: str) -> AppConfigPolicyNotFound:
    return AppConfigPolicyNotFound(extra_msg=f"config_name={config_name!r}")


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
        """Update a policy. Resolves `config_name` to the row's UUID,
        builds an ``Updater``, and delegates to the DB source. Raises
        :class:`AppConfigPolicyNotFound` when no row exists (or the
        row vanishes between resolve and write)."""
        pk_value = await self._db_source.resolve_pk_by_config_name(config_name)
        if pk_value is None:
            raise _missing(config_name)
        updater: Updater[AppConfigPolicyRow] = Updater(
            spec=AppConfigPolicyUpdaterSpec(scope_sources=scope_sources),
            pk_value=pk_value,
        )
        result = await self._db_source.update(updater)
        if result is None:
            raise _missing(config_name)
        return result

    @app_config_policy_admin_repository_resilience.apply()
    async def purge(self, config_name: str) -> bool:
        """Delete a policy by `config_name`. Resolves `config_name` to
        the row's UUID, builds a ``Purger``, and delegates to the DB
        source. Returns ``True`` only when a row was actually removed."""
        pk_value = await self._db_source.resolve_pk_by_config_name(config_name)
        if pk_value is None:
            return False
        purger: Purger[AppConfigPolicyRow] = Purger(
            row_class=AppConfigPolicyRow,
            pk_value=pk_value,
        )
        return await self._db_source.purge(purger)

    @app_config_policy_admin_repository_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        return await self._db_source.search(querier)
