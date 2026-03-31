from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RuntimeVariantPresetRepositories:
    repository: RuntimeVariantPresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=RuntimeVariantPresetRepository(args.db),
        )
