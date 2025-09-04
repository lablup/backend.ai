from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ProjectResourcePolicyRepositories:
    repository: ProjectResourcePolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ProjectResourcePolicyRepository(args.db)

        return cls(
            repository=repository,
        )
