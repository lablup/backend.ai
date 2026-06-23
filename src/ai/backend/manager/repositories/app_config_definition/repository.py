from __future__ import annotations

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_definition.types import (
    AppConfigDefinitionData,
    AppConfigDefinitionListResult,
)
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.app_config_definition.db_source import (
    AppConfigDefinitionDBSource,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Purger
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigDefinitionRepository",)

app_config_definition_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_DEFINITION_REPOSITORY,
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


class AppConfigDefinitionRepository:
    """Access to app config definitions."""

    _db_source: AppConfigDefinitionDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigDefinitionDBSource(ops_provider)

    @app_config_definition_repository_resilience.apply()
    async def create(
        self,
        creator: Creator[AppConfigDefinitionRow],
    ) -> AppConfigDefinitionData:
        return await self._db_source.create(creator)

    @app_config_definition_repository_resilience.apply()
    async def get_by_id(self, definition_id: AppConfigDefinitionID) -> AppConfigDefinitionData:
        return await self._db_source.get_by_id(definition_id)

    @app_config_definition_repository_resilience.apply()
    async def by_config_name(self, config_name: str) -> AppConfigDefinitionData:
        return await self._db_source.by_config_name(config_name)

    @app_config_definition_repository_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigDefinitionListResult:
        return await self._db_source.search(querier)

    @app_config_definition_repository_resilience.apply()
    async def purge(self, purger: Purger[AppConfigDefinitionRow]) -> AppConfigDefinitionData:
        return await self._db_source.purge(purger)
