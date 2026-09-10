"""The operations that build the permission graph.

Each write is one ops primitive, so nothing here opens a transaction: what has to land
together — a roster place and the role it grants — lands in the primitive it is
composed of.
"""

from __future__ import annotations

from typing import Any

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import UserRoleRevocationData
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.rbac.actions.relation.base import (
    RelationLinkResult,
    RelationSwitchResult,
    RelationUnlinkResult,
)
from ai.backend.manager.services.rbac.actions.relation.create import (
    CreateRelationAction,
    CreateRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.purge import (
    PurgeRelationAction,
    PurgeRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.switch import (
    DeleteRelationAction,
    DeleteRelationActionResult,
    RestoreRelationAction,
    RestoreRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.role.assign import (
    AssignRoleAction,
    AssignRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
    BulkAssignRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.bulk_revoke import (
    BulkRevokeRoleAction,
    BulkRevokeRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.revoke import (
    RevokeRoleAction,
    RevokeRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.join_project import (
    JoinProjectAction,
    JoinProjectActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.leave_project import (
    LeaveProjectAction,
    LeaveProjectActionResult,
)

__all__ = ("RbacRelationService", "RbacRoleService", "RbacRosterService")


class RbacRelationService:
    """Linking two entities and unlinking them.

    One method per direction: which relation a run is about travels on the action's
    spec, so every kind goes through the same two.
    """

    _repository: RbacRelationRepository

    def __init__(self, repository: RbacRelationRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateRelationAction[Any, Any, Any]
    ) -> CreateRelationActionResult[Any, Any]:
        written = await self._repository.create(
            [(pair.scope, pair.target) for pair in action.pairs], action.creator
        )
        return CreateRelationActionResult(
            results=[
                RelationLinkResult(pair=pair, linked=linked)
                for pair, linked in zip(action.pairs, written, strict=True)
            ]
        )

    async def purge(
        self, action: PurgeRelationAction[Any, Any, Any]
    ) -> PurgeRelationActionResult[Any, Any]:
        unlinked = await self._repository.purge(
            [(pair.scope, pair.target) for pair in action.pairs], action.purger
        )
        return PurgeRelationActionResult(
            results=[
                RelationUnlinkResult(pair=pair, unlinked=was_linked)
                for pair, was_linked in zip(action.pairs, unlinked, strict=True)
            ]
        )

    async def delete(
        self, action: DeleteRelationAction[Any, Any, Any]
    ) -> DeleteRelationActionResult[Any, Any]:
        switched = await self._repository.delete(
            [(pair.scope, pair.target) for pair in action.pairs], action.updater
        )
        return DeleteRelationActionResult(
            results=[
                RelationSwitchResult(pair=pair, switched=moved)
                for pair, moved in zip(action.pairs, switched, strict=True)
            ]
        )

    async def restore(
        self, action: RestoreRelationAction[Any, Any, Any]
    ) -> RestoreRelationActionResult[Any, Any]:
        switched = await self._repository.restore(
            [(pair.scope, pair.target) for pair in action.pairs], action.updater
        )
        return RestoreRelationActionResult(
            results=[
                RelationSwitchResult(pair=pair, switched=moved)
                for pair, moved in zip(action.pairs, switched, strict=True)
            ]
        )


class RbacRosterService:
    """Putting a user on a project's roster and taking them off."""

    _repository: RbacRosterRepository

    def __init__(self, repository: RbacRosterRepository) -> None:
        self._repository = repository

    async def join(self, action: JoinProjectAction) -> JoinProjectActionResult:
        members = await self._repository.join_members(
            action.project_id, action.user_ids, action.role_id
        )
        return JoinProjectActionResult(members=members)

    async def leave(self, action: LeaveProjectAction) -> LeaveProjectActionResult:
        result = await self._repository.leave_members(action.project_id, action.user_ids)
        return LeaveProjectActionResult(members=result.members, failures=result.failures)


class RbacRoleService:
    """Granting a role to a user and taking it back.

    A grant is a roster place as well: a user holding a role in a project is on that
    project's list, and losing the last role there takes them off it.
    """

    _repository: PermissionControllerRepository
    _roster_repository: RbacRosterRepository

    def __init__(
        self,
        repository: PermissionControllerRepository,
        roster_repository: RbacRosterRepository,
    ) -> None:
        self._repository = repository
        self._roster_repository = roster_repository

    async def assign_role(self, action: AssignRoleAction) -> AssignRoleActionResult:
        """Assigns a role to a user.

        When project_id is provided, also binds the user to the project.
        """
        if action.input.project_id is not None:
            await self._roster_repository.join_member(
                ProjectID(action.input.project_id), UserID(action.input.user_id)
            )
        data = await self._repository.assign_role(action.input)
        return AssignRoleActionResult(data=data)

    async def revoke_role(self, action: RevokeRoleAction) -> RevokeRoleActionResult:
        """Revokes a role from a user.

        If the role was project-scoped and no remaining roles exist in that
        project, the user is also removed from the project.
        """
        result = await self._repository.revoke_role(action.input)
        for prc in result.project_remaining_roles:
            if prc.remaining_count == 0:
                await self._roster_repository.leave_member(
                    ProjectID(prc.project_id), UserID(action.input.user_id)
                )
        return RevokeRoleActionResult(
            data=UserRoleRevocationData(
                user_role_id=result.user_role_id,
                user_id=action.input.user_id,
                role_id=action.input.role_id,
            )
        )

    async def bulk_assign_role(self, action: BulkAssignRoleAction) -> BulkAssignRoleActionResult:
        """Assigns a role to multiple users.

        When project_id is provided, also binds each user to the project.
        """
        if action.project_id is not None:
            for user_id in action.user_ids:
                await self._roster_repository.join_member(ProjectID(action.project_id), user_id)
        data = await self._repository.bulk_assign_role(
            action.role_id, action.user_ids, action.granted_by
        )
        return BulkAssignRoleActionResult(data=data)

    async def bulk_revoke_role(self, action: BulkRevokeRoleAction) -> BulkRevokeRoleActionResult:
        """Revokes a role from multiple users with partial failure support."""
        data = await self._repository.bulk_revoke_role(action.input)
        return BulkRevokeRoleActionResult(data=data)
