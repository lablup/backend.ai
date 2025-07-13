from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)


@dataclass
class KeypairResourcePolicyRepositories:
    repository: KeypairResourcePolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = KeypairResourcePolicyRepository(args.db)

        return cls(
            repository=repository,
        )
