from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RuntimeVariantRepositories:
    repository: RuntimeVariantRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=RuntimeVariantRepository(args.db),
        )
