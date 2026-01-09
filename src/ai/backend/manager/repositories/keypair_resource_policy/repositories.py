from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class KeypairResourcePolicyRepositories:
    repository: KeypairResourcePolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = KeypairResourcePolicyRepository(args.db)

        return cls(
            repository=repository,
        )
