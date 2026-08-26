"""Links between entities, membership of an organization, and the roles that come with it.

One service: all three answer the same kind of question — who may put these two things
together — and putting a user in an organization writes a link and grants a role in one
transaction, so splitting them would split that transaction too.

A link is generic in what it writes: a domain declares the spec that says which table and
which columns, declares its own action carrying that spec, and hands the function that
calls this. What is not generic is the permission, which is why the operation lives here
rather than on a generic ops path.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md` and BEP-1076.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.repositories.rbac.repository import RBACRepository

__all__ = ("RBACService",)


class RBACService:
    """Linking entities, putting users in organizations, and the roles they hold."""

    _repository: RBACRepository

    def __init__(self, repository: RBACRepository) -> None:
        self._repository = repository

    # -- links --------------------------------------------------------------------

    async def create_relation(
        self, left: EntityIdentifier, right: EntityIdentifier, creator: RelationCreator[Any]
    ) -> bool:
        """Link the two entities; ``False`` when the pair was already linked."""
        return await self._repository.create_relation(left, right, creator)

    async def delete_relation(
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[Any],
    ) -> bool:
        """Switch the pair's relation off; ``False`` when there was none to switch."""
        return await self._repository.delete_relation(left, right, updater)

    async def restore_relation(
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[Any],
    ) -> bool:
        """Switch the pair's relation back on; ``False`` when there was none."""
        return await self._repository.restore_relation(left, right, updater)

    async def purge_relation(
        self, left: EntityIdentifier, right: EntityIdentifier, purger: RelationPurger[Any]
    ) -> bool:
        """Remove the row linking the pair; ``False`` when there was none to remove."""
        return await self._repository.purge_relation(left, right, purger)

    # -- membership ---------------------------------------------------------------

    async def enroll(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        creator: RelationCreator[Any],
        role_ids: Sequence[RoleID] | None = None,
        granted_by: UserID | None = None,
    ) -> bool:
        """Put the user in the organization and give them its roles.

        ``role_ids`` names what to give; ``None`` gives the organization's auto-assign
        roles. A named role the organization does not hold is refused, in the same
        transaction that writes — membership must not become a path for attaching an
        unrelated role.
        """
        return await self._repository.enroll(organization, user_id, creator, role_ids, granted_by)

    async def withdraw(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        purger: RelationPurger[Any],
    ) -> bool:
        """Take the user out of the organization, and its roles with them."""
        return await self._repository.withdraw(organization, user_id, purger)

    # -- roles --------------------------------------------------------------------

    async def grant_roles(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        role_ids: Sequence[RoleID],
        granted_by: UserID | None = None,
    ) -> None:
        """Give a member roles of that organization, without touching the membership."""
        await self._repository.grant_roles(organization, user_id, role_ids, granted_by)

    async def revoke_roles(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        role_ids: Sequence[RoleID],
    ) -> None:
        """Take roles of that organization back from a member."""
        await self._repository.revoke_roles(organization, user_id, role_ids)
