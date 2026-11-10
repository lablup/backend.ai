from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from .repository import ServiceCatalogRepository

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ServiceCatalogRepositories:
    repository: ServiceCatalogRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=ServiceCatalogRepository(args.v2_ops_provider))
