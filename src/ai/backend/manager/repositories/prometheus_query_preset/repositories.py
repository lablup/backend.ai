from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class PrometheusQueryPresetRepositories:
    repository: PrometheusQueryPresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = PrometheusQueryPresetRepository(args.db)

        return cls(
            repository=repository,
        )
