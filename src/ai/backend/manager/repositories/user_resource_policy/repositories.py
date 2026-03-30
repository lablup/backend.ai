from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)


@dataclass
class UserResourcePolicyRepositories:
    repository: UserResourcePolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = UserResourcePolicyRepository(args.db)

        return cls(
            repository=repository,
        )
