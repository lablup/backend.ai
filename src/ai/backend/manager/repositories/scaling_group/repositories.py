from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ScalingGroupRepositories:
    repository: ScalingGroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ScalingGroupRepository(args.db)

        return cls(
            repository=repository,
        )
