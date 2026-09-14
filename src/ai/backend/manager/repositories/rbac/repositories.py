from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RbacRepositories:
    relation: RbacRelationRepository
    roster: RbacRosterRepository
    permission_check: RbacPermissionCheckRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            relation=RbacRelationRepository(args.relation_ops_provider),
            roster=RbacRosterRepository(RosterOpsProvider(args.db)),
            permission_check=RbacPermissionCheckRepository(PermissionOpsProvider(args.db)),
        )
