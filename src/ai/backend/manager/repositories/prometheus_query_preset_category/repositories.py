from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.prometheus_query_preset_category.repository import (
    PrometheusQueryPresetCategoryRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class PrometheusQueryPresetCategoryRepositories:
    repository: PrometheusQueryPresetCategoryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = PrometheusQueryPresetCategoryRepository(args.db)
        return cls(repository=repository)
