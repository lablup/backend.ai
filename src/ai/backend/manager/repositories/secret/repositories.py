from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SecretRepositories:
    repository: SecretRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=SecretRepository(args.secret_ops_provider, args.key_provider_pool),
        )
