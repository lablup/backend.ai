from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs

from .repository import (
    KeypairResourcePolicyRepository,
    ProjectResourcePolicyRepository,
    UserResourcePolicyRepository,
)


@dataclass
class ResourcePolicyRepositories:
    keypair_resource_policy: KeypairResourcePolicyRepository
    project_resource_policy: ProjectResourcePolicyRepository
    user_resource_policy: UserResourcePolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        keypair_resource_policy = KeypairResourcePolicyRepository(args.db)
        project_resource_policy = ProjectResourcePolicyRepository(args.db)
        user_resource_policy = UserResourcePolicyRepository(args.db)

        return cls(
            keypair_resource_policy=keypair_resource_policy,
            project_resource_policy=project_resource_policy,
            user_resource_policy=user_resource_policy,
        )
