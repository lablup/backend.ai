from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    ResolvedAppConfigScope,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Updater,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider

__all__ = ("AppConfigFragmentRepository",)

app_config_fragment_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_FRAGMENT_REPOSITORY,
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


class AppConfigFragmentRepository:
    """Access to app config fragments."""

    _db_source: AppConfigFragmentDBSource

    def __init__(self, ops_provider: RBACOpsProvider) -> None:
        self._db_source = AppConfigFragmentDBSource(ops_provider)

    @app_config_fragment_repository_resilience.apply()
    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        return await self._db_source.create(spec)

    @app_config_fragment_repository_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        return await self._db_source.get_by_id(fragment_id)

    @app_config_fragment_repository_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        return await self._db_source.update(updater)

    @app_config_fragment_repository_resilience.apply()
    async def purge(self, purger_spec: AppConfigFragmentPurgerSpec) -> AppConfigFragmentData:
        return await self._db_source.purge(purger_spec)

    @app_config_fragment_repository_resilience.apply()
    async def admin_search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    @app_config_fragment_repository_resilience.apply()
    async def batch_load_by_ids(
        self, fragment_ids: Sequence[AppConfigFragmentID]
    ) -> Sequence[AppConfigFragmentData]:
        return await self._db_source.batch_load_by_ids(fragment_ids)

    @app_config_fragment_repository_resilience.apply()
    async def scoped_search(
        self, querier: BatchQuerier, scopes: Sequence[SearchScope]
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.scoped_search(querier, scopes)

    @app_config_fragment_repository_resilience.apply()
    async def bulk_update(
        self,
        updaters: Sequence[Updater[AppConfigFragmentRow]],
    ) -> AppConfigFragmentBulkResult:
        return await self._db_source.bulk_update(updaters)

    @app_config_fragment_repository_resilience.apply()
    async def bulk_purge(
        self,
        purger_specs: Sequence[AppConfigFragmentPurgerSpec],
    ) -> AppConfigFragmentBulkResult:
        return await self._db_source.bulk_purge(purger_specs)

    @app_config_fragment_repository_resilience.apply()
    async def list_visible_fragments_bulk(
        self, config_names: list[str], scope: ResolvedAppConfigScope | None = None
    ) -> list[AppConfigFragmentData]:
        return await self._db_source.list_visible_fragments_bulk(config_names, scope)
