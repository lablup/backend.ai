from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.retention_policy.repository import RetentionPolicyRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RetentionPolicyRepositories:
    repository: RetentionPolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=RetentionPolicyRepository(args.ops_provider),
        )
