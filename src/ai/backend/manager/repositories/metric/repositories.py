from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.prometheus_query_preset.db_source import (
    PrometheusQueryPresetDBSource,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class MetricRepositories:
    repository: MetricRepository

    @classmethod
    def create(
        cls,
        args: RepositoryArgs,
        prometheus_query_preset_db_source: PrometheusQueryPresetDBSource,
    ) -> Self:
        return cls(
            repository=MetricRepository(
                prometheus_client=args.prometheus_client,
                prometheus_query_preset_db_source=prometheus_query_preset_db_source,
            ),
        )
