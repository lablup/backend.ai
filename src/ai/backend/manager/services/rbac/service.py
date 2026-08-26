"""Links between entities, membership of an organization, and the roles that come with it.

One service: all three answer the same kind of question — who may put these two things
together — and putting a user in an organization writes a link and grants a role in one
transaction, so splitting them would split that transaction too.

A link is generic in what it writes: the spec saying which table and which columns is a
value on the action, so one wiring serves every relation. What is not generic is the
permission, which is why the operation lives here rather than on a generic ops path.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md` and BEP-1076.
"""

from __future__ import annotations

from typing import Any

from ai.backend.manager.repositories.rbac.repository import RBACRepository
from ai.backend.manager.services.rbac.actions.create_relation import (
    CreateRelationAction,
    CreateRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.delete_relation import (
    DeleteRelationAction,
    DeleteRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.enroll import EnrollAction, EnrollActionResult
from ai.backend.manager.services.rbac.actions.grant_roles import (
    GrantRolesAction,
    GrantRolesActionResult,
)
from ai.backend.manager.services.rbac.actions.purge_relation import (
    PurgeRelationAction,
    PurgeRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.restore_relation import (
    RestoreRelationAction,
    RestoreRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.revoke_roles import (
    RevokeRolesAction,
    RevokeRolesActionResult,
)
from ai.backend.manager.services.rbac.actions.withdraw import (
    WithdrawAction,
    WithdrawActionResult,
)

__all__ = ("RBACService",)


class RBACService:
    """Linking entities, putting users in organizations, and the roles they hold."""

    _repository: RBACRepository

    def __init__(self, repository: RBACRepository) -> None:
        self._repository = repository

    # -- links --------------------------------------------------------------------

    async def create_relation(
        self, action: CreateRelationAction[Any]
    ) -> CreateRelationActionResult:
        created = await self._repository.create_relation(action.left, action.right, action.creator)
        return CreateRelationActionResult(created=created)

    async def delete_relation(
        self, action: DeleteRelationAction[Any]
    ) -> DeleteRelationActionResult:
        deleted = await self._repository.delete_relation(action.left, action.right, action.updater)
        return DeleteRelationActionResult(deleted=deleted)

    async def restore_relation(
        self, action: RestoreRelationAction[Any]
    ) -> RestoreRelationActionResult:
        restored = await self._repository.restore_relation(
            action.left, action.right, action.updater
        )
        return RestoreRelationActionResult(restored=restored)

    async def purge_relation(self, action: PurgeRelationAction[Any]) -> PurgeRelationActionResult:
        purged = await self._repository.purge_relation(action.left, action.right, action.purger)
        return PurgeRelationActionResult(purged=purged)

    # -- membership ---------------------------------------------------------------

    async def enroll(self, action: EnrollAction[Any]) -> EnrollActionResult:
        enrolled = await self._repository.enroll(
            action.organization,
            action.user_id,
            action.creator,
            action.granted_by,
            action.role_ids,
        )
        return EnrollActionResult(user_id=action.user_id, enrolled=enrolled)

    async def withdraw(self, action: WithdrawAction[Any]) -> WithdrawActionResult:
        withdrawn = await self._repository.withdraw(
            action.organization, action.user_id, action.purger
        )
        return WithdrawActionResult(user_id=action.user_id, withdrawn=withdrawn)

    # -- roles --------------------------------------------------------------------

    async def grant_roles(self, action: GrantRolesAction) -> GrantRolesActionResult:
        await self._repository.grant_roles(
            action.organization, action.user_id, action.role_ids, action.granted_by
        )
        return GrantRolesActionResult(user_id=action.user_id)

    async def revoke_roles(self, action: RevokeRolesAction) -> RevokeRolesActionResult:
        await self._repository.revoke_roles(action.organization, action.user_id, action.role_ids)
        return RevokeRolesActionResult(user_id=action.user_id)
