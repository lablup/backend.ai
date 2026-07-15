from __future__ import annotations

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigAllowListSearchResult,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.db_source import (
    AppConfigAllowListDBSource,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Purger,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigAllowListRepository",)

app_config_allow_list_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_ALLOW_LIST_REPOSITORY,
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


class AppConfigAllowListRepository:
    """Access to app config allow-list entries."""

    _db_source: AppConfigAllowListDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigAllowListDBSource(ops_provider)

    @app_config_allow_list_repository_resilience.apply()
    async def create(
        self,
        creator: Creator[AppConfigAllowListRow],
    ) -> AppConfigAllowListData:
        return await self._db_source.create(creator)

    @app_config_allow_list_repository_resilience.apply()
    async def get_by_id(self, allow_list_id: AppConfigAllowListID) -> AppConfigAllowListData:
        return await self._db_source.get_by_id(allow_list_id)

    @app_config_allow_list_repository_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigAllowListSearchResult:
        return await self._db_source.search(querier)

    @app_config_allow_list_repository_resilience.apply()
    async def update(self, updater: Updater[AppConfigAllowListRow]) -> AppConfigAllowListData:
        return await self._db_source.update(updater)

    @app_config_allow_list_repository_resilience.apply()
    async def purge(self, purger: Purger[AppConfigAllowListRow]) -> AppConfigAllowListData:
        return await self._db_source.purge(purger)
