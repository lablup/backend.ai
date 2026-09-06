from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.entity_invitation.repository import EntityInvitationRepository
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class EntityInvitationRepositories:
    repository: EntityInvitationRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=EntityInvitationRepository(ShareOpsProvider(args.db)),
        )
