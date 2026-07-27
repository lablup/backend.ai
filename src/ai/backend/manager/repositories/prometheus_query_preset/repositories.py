from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.prometheus_query_preset.db_source import (
    PrometheusQueryPresetDBSource,
)
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class PrometheusQueryPresetRepositories:
    repository: PrometheusQueryPresetRepository

    @classmethod
    def create(
        cls,
        args: RepositoryArgs,
        db_source: PrometheusQueryPresetDBSource,
    ) -> Self:
        repository = PrometheusQueryPresetRepository(db_source, args.prometheus_client)

        return cls(
            repository=repository,
        )
