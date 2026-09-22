from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user.repository import UserRepository


@dataclass
class UserRepositories:
    repository: UserRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = UserRepository(
            args.db,
            args.v2_ops_provider,
            ShareOpsProvider(args.db),
            ResourcePolicyOpsProvider(args.db),
            args.key_provider_pool,
        )

        return cls(
            repository=repository,
        )
