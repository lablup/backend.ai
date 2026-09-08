from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RbacRepositories:
    relation: RbacRelationRepository
    roster: RbacRosterRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            relation=RbacRelationRepository(args.relation_ops_provider),
            roster=RbacRosterRepository(RosterOpsProvider(args.db)),
        )
